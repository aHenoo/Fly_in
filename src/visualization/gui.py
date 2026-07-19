"""Tkinter graphical interface for the Fly-in simulation."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from src.graph.graph import Graph
from src.graph.zone import Zone, ZoneType
from src.simulation.drone import DroneStatus
from src.simulation.simulation import Simulation, SimulationError


class GUIError(Exception):
    """Raised when the graphical interface cannot be initialized."""


class SimulationGUI:
    """Display a graph and animate its drones turn by turn."""

    ZONE_COLORS = {
        "black": "#303030",
        "red": "#ef5350",
        "green": "#66bb6a",
        "yellow": "#fdd835",
        "blue": "#42a5f5",
        "purple": "#ab47bc",
        "magenta": "#ec407a",
        "cyan": "#26c6da",
        "white": "#fafafa",
        "gray": "#9e9e9e",
        "grey": "#9e9e9e",
        "orange": "#ffa726",
        "gold": "#ffca28",
        "lime": "#9ccc65",
        "brown": "#8d6e63",
        "darkred": "#b71c1c",
        "maroon": "#8e244d",
        "violet": "#7e57c2",
        "crimson": "#d32f2f",
        "rainbow": "#ec407a",
    }
    TYPE_COLORS = {
        ZoneType.NORMAL: "#42a5f5",
        ZoneType.PRIORITY: "#26c6da",
        ZoneType.RESTRICTED: "#ffa726",
        ZoneType.BLOCKED: "#616161",
    }

    def __init__(self, graph: Graph, simulation: Simulation) -> None:
        """Create the controls and drawing canvas."""
        self.graph = graph
        self.simulation = simulation
        self.turn = 0
        self.playing = False
        self.animating = False
        self.animation_id = 0
        self.last_movement = "Ready"
        self.drone_positions = self._initial_drone_positions()

        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            raise GUIError(str(error)) from error
        self.root.title("Fly-in - Drone Simulation")
        self.root.geometry("1100x760")
        self.root.minsize(760, 520)
        self.root.configure(background="#000000")
        self._configure_style()

        self._build_layout()
        self.root.after_idle(self._draw)

    def run(self) -> None:
        """Start Tkinter's event loop."""
        self.root.mainloop()

    def _configure_style(self) -> None:
        """Apply the dark theme used by the whole application window."""
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Fly.TFrame", background="#000000")
        style.configure(
            "Fly.TLabel",
            background="#000000",
            foreground="#f5f5f5",
        )
        style.configure(
            "Fly.TButton",
            background="#202020",
            foreground="#ffffff",
            bordercolor="#555555",
            lightcolor="#202020",
            darkcolor="#202020",
            padding=(10, 6),
        )
        style.map(
            "Fly.TButton",
            background=[
                ("active", "#383838"),
                ("disabled", "#101010"),
            ],
            foreground=[("disabled", "#777777")],
        )
        style.configure(
            "Fly.Horizontal.TScale",
            background="#000000",
            troughcolor="#333333",
        )

    def _build_layout(self) -> None:
        """Build header, canvas, legend, and playback controls."""
        header = ttk.Frame(
            self.root,
            padding=(12, 10),
            style="Fly.TFrame",
        )
        header.pack(fill="x")

        ttk.Label(
            header,
            text="FLY-IN",
            font=("TkDefaultFont", 20, "bold"),
            style="Fly.TLabel",
        ).pack(side="left")
        self.status_label = ttk.Label(
            header,
            font=("TkDefaultFont", 11),
            style="Fly.TLabel",
        )
        self.status_label.pack(side="right")

        self.canvas = tk.Canvas(
            self.root,
            background="#000000",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=12)
        self.canvas.bind("<Configure>", lambda _event: self._draw())

        legend = ttk.Label(
            self.root,
            text=(
                "● Normal    ◆ Priority    ◉ Restricted    ■ Blocked    "
                "Green border: start    Red border: end"
            ),
            anchor="center",
            padding=(8, 6),
            style="Fly.TLabel",
        )
        legend.pack(fill="x")

        controls = ttk.Frame(
            self.root,
            padding=(12, 8),
            style="Fly.TFrame",
        )
        controls.pack(fill="x")

        self.next_button = ttk.Button(
            controls,
            text="Next turn",
            command=self._next_turn,
            style="Fly.TButton",
        )
        self.next_button.pack(side="left", padx=(0, 6))

        self.play_button = ttk.Button(
            controls,
            text="Auto play",
            command=self._toggle_play,
            style="Fly.TButton",
        )
        self.play_button.pack(side="left")

        self.restart_button = ttk.Button(
            controls,
            text="Restart",
            command=self._restart,
            style="Fly.TButton",
        )
        self.restart_button.pack(side="left", padx=(6, 0))

        ttk.Label(
            controls,
            text="Speed:",
            style="Fly.TLabel",
        ).pack(side="left", padx=(20, 6))
        self.speed = tk.DoubleVar(value=1.0)
        ttk.Scale(
            controls,
            from_=0.25,
            to=2.0,
            variable=self.speed,
            orient="horizontal",
            length=160,
            style="Fly.Horizontal.TScale",
        ).pack(side="left")

        self.movement_label = ttk.Label(
            controls,
            text=self.last_movement,
            anchor="e",
            style="Fly.TLabel",
        )
        self.movement_label.pack(side="right", fill="x", expand=True)
        self._update_status()

    def _next_turn(self) -> None:
        """Advance the simulation once and refresh the canvas."""
        if self.simulation.is_complete() or self.animating:
            return
        start_positions = dict(self.drone_positions)
        try:
            self.last_movement = self.simulation.run_turn()
        except SimulationError as error:
            self.playing = False
            messagebox.showerror("Simulation error", str(error))
            return

        self.turn += 1
        self.movement_label.configure(
            text=f"Turn {self.turn}: {self.last_movement}",
        )
        target_positions = self._simulation_drone_positions()
        self._start_animation(start_positions, target_positions)

    def _toggle_play(self) -> None:
        """Start or pause automatic playback."""
        self.playing = not self.playing
        self.play_button.configure(
            text="Pause" if self.playing else "Auto play",
        )
        if self.playing:
            self._auto_step()

    def _restart(self) -> None:
        """Reset every drone and return to the first turn."""
        self.playing = False
        self.animating = False
        self.animation_id += 1
        self.simulation = Simulation(
            self.graph,
            self.simulation.nb_drones,
        )
        self.drone_positions = self._initial_drone_positions()
        self.turn = 0
        self.last_movement = "Ready"
        self.play_button.configure(text="Auto play", state="normal")
        self.next_button.configure(state="normal")
        self.movement_label.configure(text=self.last_movement)
        self._update_status()
        self._draw()

    def _auto_step(self) -> None:
        """Schedule turns without blocking Tkinter's event loop."""
        if (
            not self.playing
            or self.animating
            or self.simulation.is_complete()
        ):
            return
        self._next_turn()

    def _start_animation(
        self,
        starts: dict[int, tuple[float, float]],
        targets: dict[int, tuple[float, float]],
    ) -> None:
        """Interpolate every drone between its old and new position."""
        self.animating = True
        self.animation_id += 1
        current_animation = self.animation_id
        self.next_button.configure(state="disabled")
        frames = 24
        duration = max(180, int(700 / self.speed.get()))
        frame_delay = max(10, duration // frames)

        def draw_frame(frame: int) -> None:
            if current_animation != self.animation_id:
                return
            progress = frame / frames
            eased = progress * progress * (3 - 2 * progress)
            for identifier, start in starts.items():
                target = targets[identifier]
                self.drone_positions[identifier] = (
                    start[0] + (target[0] - start[0]) * eased,
                    start[1] + (target[1] - start[1]) * eased,
                )
            self._draw()
            if frame < frames:
                self.root.after(
                    frame_delay,
                    lambda: draw_frame(frame + 1),
                )
            else:
                self._finish_animation(targets)

        draw_frame(1)

    def _finish_animation(
        self,
        targets: dict[int, tuple[float, float]],
    ) -> None:
        """Commit animated positions and continue automatic playback."""
        self.drone_positions = dict(targets)
        self.animating = False
        self._update_status()
        self._draw()

        if self.simulation.is_complete():
            self.playing = False
            self.play_button.configure(text="Auto play", state="disabled")
            self.next_button.configure(state="disabled")
            return

        self.next_button.configure(state="normal")
        if self.playing:
            delay = max(100, int(500 / self.speed.get()))
            self.root.after(delay, self._auto_step)

    def _update_status(self) -> None:
        """Update turn and delivery counters."""
        delivered = sum(
            drone.is_delivered()
            for drone in self.simulation.drones
        )
        self.status_label.configure(
            text=(
                f"Turn {self.turn}    "
                f"Delivered {delivered}/{self.simulation.nb_drones}"
            ),
        )

    def _draw(self) -> None:
        """Redraw connections, zones, and current drone positions."""
        if not hasattr(self, "canvas"):
            return
        self.canvas.delete("all")
        positions = self._screen_positions()

        for connection in self.graph.connections.values():
            start = positions[connection.zone_a]
            end = positions[connection.zone_b]
            self.canvas.create_line(
                *start,
                *end,
                fill="#78909c",
                width=2,
            )
            middle_x = (start[0] + end[0]) / 2
            middle_y = (start[1] + end[1]) / 2
            if connection.max_link_capacity > 1:
                self.canvas.create_text(
                    middle_x,
                    middle_y - 9,
                    text=f"link cap {connection.max_link_capacity}",
                    fill="#cfd8dc",
                    font=("TkDefaultFont", 8),
                )

        for zone in self.graph.zones.values():
            self._draw_zone(zone, positions[zone.name])
        self._draw_drones()

    def _screen_positions(self) -> dict[str, tuple[float, float]]:
        """Scale map coordinates to the currently available canvas."""
        return {
            zone.name: self._coordinate_to_screen(zone.x, zone.y)
            for zone in self.graph.zones.values()
        }

    def _coordinate_to_screen(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        """Convert one map coordinate to a canvas position."""
        width = max(self.canvas.winfo_width(), 700)
        height = max(self.canvas.winfo_height(), 380)
        padding_x = 90
        padding_y = 75
        xs = [zone.x for zone in self.graph.zones.values()]
        ys = [zone.y for zone in self.graph.zones.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        range_x = max(max_x - min_x, 1)
        range_y = max(max_y - min_y, 1)

        screen_x = padding_x + (
            (x - min_x) / range_x * (width - 2 * padding_x)
        )
        screen_y = padding_y + (
            (max_y - y) / range_y * (height - 2 * padding_y)
        )
        return (screen_x, screen_y)

    def _draw_zone(
        self,
        zone: Zone,
        position: tuple[float, float],
    ) -> None:
        """Draw one zone with its type, name, and capacity."""
        x, y = position
        radius = 23
        fill = self._zone_color(zone)
        outline = "#eceff1"
        width = 2
        if zone.name == self.graph.start_name:
            outline, width = "#66bb6a", 5
        elif zone.name == self.graph.end_name:
            outline, width = "#ef5350", 5

        if zone.zone_type is ZoneType.BLOCKED:
            self.canvas.create_rectangle(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill=fill,
                outline=outline,
                width=width,
            )
        else:
            self.canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill=fill,
                outline=outline,
                width=width,
            )

        symbol = {
            ZoneType.NORMAL: "N",
            ZoneType.PRIORITY: "P",
            ZoneType.RESTRICTED: "R",
            ZoneType.BLOCKED: "X",
        }[zone.zone_type]
        self.canvas.create_text(
            x,
            y,
            text=symbol,
            fill="#ffffff",
            font=("TkDefaultFont", 11, "bold"),
        )
        capacity = "unlimited" if zone.name in (
            self.graph.start_name,
            self.graph.end_name,
        ) else f"capacity {zone.max_drones}"
        self.canvas.create_text(
            x,
            y + 36,
            text=f"{zone.name}\n{capacity}",
            fill="#eceff1",
            justify="center",
            font=("TkDefaultFont", 9, "bold"),
        )

    def _draw_drones(self) -> None:
        """Draw drone labels at zones or midway along active links."""
        grouped: dict[tuple[float, float], list[str]] = {}
        for drone in self.simulation.drones:
            map_position = self.drone_positions[drone.identifier]
            position = self._coordinate_to_screen(*map_position)
            grouped.setdefault(position, []).append(drone.get_label())

        for (x, y), labels in grouped.items():
            text = ", ".join(labels)
            self.canvas.create_rectangle(
                x - 28,
                y - 39,
                x + 28,
                y - 23,
                fill="#ffffff",
                outline="#263238",
            )
            self.canvas.create_text(
                x,
                y - 31,
                text=text,
                fill="#101820",
                font=("TkDefaultFont", 8, "bold"),
            )

    def _initial_drone_positions(self) -> dict[int, tuple[float, float]]:
        """Place every drone on its current zone."""
        return {
            drone.identifier: self._zone_coordinates(drone.current_zone)
            for drone in self.simulation.drones
        }

    def _simulation_drone_positions(
        self,
    ) -> dict[int, tuple[float, float]]:
        """Return visual targets for the simulation's current state."""
        targets: dict[int, tuple[float, float]] = {}
        for drone in self.simulation.drones:
            current = self._zone_coordinates(drone.current_zone)
            if (
                drone.status is DroneStatus.MOVING
                and drone.target_zone is not None
            ):
                target = self._zone_coordinates(drone.target_zone)
                current = (
                    (current[0] + target[0]) / 2,
                    (current[1] + target[1]) / 2,
                )
            targets[drone.identifier] = current
        return targets

    def _zone_coordinates(self, zone_name: str) -> tuple[float, float]:
        """Return the original coordinates of a zone."""
        zone = self.graph.get_zone(zone_name)
        return (float(zone.x), float(zone.y))

    def _zone_color(self, zone: Zone) -> str:
        """Return a Tk-compatible metadata or type fallback color."""
        if zone.color is not None:
            known_color = self.ZONE_COLORS.get(zone.color.lower())
            if known_color is not None:
                return known_color
        return self.TYPE_COLORS[zone.zone_type]

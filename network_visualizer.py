import tkinter as tk
from tkinter import ttk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from typing import Dict, Optional
import random

class NetworkVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Satellite Network Visualizer")
        
        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create visualization area
        self.viz_frame = ttk.Frame(self.main_container)
        self.viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create control panel
        self.control_panel = ttk.Frame(self.main_container, width=200)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initialize network graph
        self.graph = nx.Graph()
        self.figure = Figure(figsize=(8, 6))
        self.ax = self.figure.add_subplot(111)
        
        # Create canvas for matplotlib
        self.canvas = FigureCanvasTkAgg(self.figure, self.viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize control panel elements
        self.init_control_panel()
        
        # Network data
        self.network = None
        self.selected_satellite = None
        
    def init_control_panel(self):
        """Initialize control panel widgets"""
        # Satellite selection
        ttk.Label(self.control_panel, text="Select Satellite:").pack(pady=5)
        self.satellite_var = tk.StringVar()
        self.satellite_select = ttk.Combobox(
            self.control_panel, 
            textvariable=self.satellite_var
        )
        self.satellite_select.pack(pady=5)
        
        # Satellite info
        self.info_frame = ttk.LabelFrame(self.control_panel, text="Satellite Info")
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)
        self.info_text = tk.Text(self.info_frame, height=10, width=25)
        self.info_text.pack(padx=5, pady=5)
        
        # Update button
        ttk.Button(
            self.control_panel, 
            text="Refresh View",
            command=self.update_visualization
        ).pack(pady=5)
        
    def set_network(self, network):
        """Set the network to visualize"""
        self.network = network
        self.update_satellite_list()
        self.update_visualization()
        
    def update_satellite_list(self):
        """Update satellite selection dropdown"""
        if self.network:
            satellites = list(self.network.satellites.keys())
            self.satellite_select['values'] = satellites
            if satellites:
                self.satellite_select.set(satellites[0])
                
    def get_orbit_position(self, sat_id: str):
        """
        Calculate position based on orbital plane and satellite number
        
        Args:
            sat_id: Satellite ID (e.g., 'LEO_01', 'LEO_09', etc.)
        
        Returns:
            tuple: (x, y) normalized coordinates
        """
        try:
            # Extract satellite number
            sat_num = int(sat_id.split('_')[1])
            
            # Calculate orbit number (0-based)
            orbit_num = (sat_num - 1) // 8
            
            # Calculate position within orbit (0-7)
            position_in_orbit = (sat_num - 1) % 8
            
            # Calculate coordinates
            # X: spread orbits horizontally (-1 to 1)
            # Y: distribute satellites in each orbit (-1 to 1)
            x = (orbit_num / 2) - 0.5  # Normalize orbit position
            y = (position_in_orbit / 7) - 0.5  # Normalize position in orbit
            
            return (x, y)
        except:
            # Fallback to random position if ID format is unexpected
            return (random.uniform(-1, 1), random.uniform(-1, 1))

    def update_visualization(self):
        """Update network visualization"""
        if not self.network:
            return
            
        self.graph.clear()
        self.ax.clear()
        
        # Add nodes (satellites)
        positions = {}
        for sat_id, satellite in self.network.satellites.items():
            self.graph.add_node(sat_id)
            # Use orbital position instead of geographic coordinates
            positions[sat_id] = self.get_orbit_position(sat_id)
            
        # Add edges (connections)
        edges = []
        edge_colors = []
        edge_widths = []
        
        for sat_id, satellite in self.network.satellites.items():
            for neighbor_id, neighbor_info in satellite.neighbors.items():
                edges.append((sat_id, neighbor_id))
                # Color based on link quality
                link_quality = neighbor_info['link_quality']
                edge_colors.append('g' if link_quality > 0.7 else 'y')
                edge_widths.append(link_quality * 2)
        
        # Draw network
        self.ax.set_title("Satellite Network Topology")
        
        # Draw nodes (satellites)
        nx.draw_networkx_nodes(
            self.graph,
            positions,
            node_color='lightblue',
            node_size=500,
            ax=self.ax
        )
        
        # Draw edges (connections)
        nx.draw_networkx_edges(
            self.graph,
            positions,
            edgelist=edges,
            edge_color=edge_colors,
            width=edge_widths,
            ax=self.ax
        )
        
        # Draw labels
        nx.draw_networkx_labels(
            self.graph,
            positions,
            font_size=8,
            ax=self.ax
        )
        
        # Add orbit labels
        for orbit in range(3):  # Assuming 3 orbits
            self.ax.text(
                orbit/2 - 0.5, 
                -0.7, 
                f'Orbit {orbit+1}',
                horizontalalignment='center'
            )
        
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)
        self.canvas.draw()
        
    def update_satellite_info(self, satellite_id: str):
        """Update satellite information display"""
        if not self.network or satellite_id not in self.network.satellites:
            return
            
        satellite = self.network.satellites[satellite_id]
        info = (f"Satellite ID: {satellite_id}\n"
                f"Position: {satellite.coordinates}\n"
                f"Active neighbors: {len(satellite.neighbors)}\n"
                f"Bandwidth: {satellite.metadata.bandwidth_capacity} Mbps\n"
                f"Processing: {satellite.metadata.processing_power} GHz")
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info)
        
    def highlight_path(self, source: str, destination: str):
        """Highlight routing path between two satellites"""
        # This will be implemented in the next step
        pass

def create_visualizer(network):
    """Create and run the network visualizer"""
    root = tk.Tk()
    app = NetworkVisualizer(root)
    app.set_network(network)
    return app, root 
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import random
import uuid
from datetime import datetime, timedelta
import heapq

@dataclass
class SatelliteMetadata:
    """Metadata class to store satellite capabilities and parameters"""
    computational_capacity: float  # MIPS (Million Instructions Per Second)
    bandwidth_capacity: float     # Mbps
    processing_power: float       # GHz
    communication_range: float    # km
    
    # Performance Metrics
    packet_loss_rate: float = 0.0      # Percentage (0-1)
    transmission_delay: float = 0.0     # milliseconds
    buffer_size: int = 1024            # KB
    queue_capacity: int = 1000         # Number of packets
    
    # Communication Parameters
    max_bandwidth_utilization: float = 0.8  # Percentage (0-1)
    min_signal_strength: float = -90.0      # dBm
    frequency_band: str = "Ka"              # Default Ka band
    modulation_scheme: str = "QPSK"         # Default modulation
    
    # Performance Tracking
    total_packets_sent: int = 0
    total_packets_received: int = 0
    successful_transmission_rate: float = 1.0  # Percentage (0-1)
    
    def calculate_throughput(self) -> float:
        """Calculate current throughput based on bandwidth and utilization"""
        return self.bandwidth_capacity * self.max_bandwidth_utilization
    
    def update_transmission_stats(self, packets_sent: int, packets_received: int):
        """Update transmission statistics"""
        self.total_packets_sent += packets_sent
        self.total_packets_received += packets_received
        if self.total_packets_sent > 0:
            self.successful_transmission_rate = (
                self.total_packets_received / self.total_packets_sent
            )

@dataclass
class RouteInfo:
    """Information about a route to a destination"""
    destination: str
    next_hop: str
    cost: float
    timestamp: datetime
    valid_until: datetime
    sequence_num: int

class RoutingUpdate:
    """Message containing routing information updates"""
    def __init__(self, sender_id: str, sequence_num: int):
        self.sender_id = sender_id
        self.sequence_num = sequence_num
        self.timestamp = datetime.now()
        self.routes: Dict[str, RouteInfo] = {}

class Satellite:
    def __init__(self, satellite_id: str):
        """
        Initialize a satellite with its basic parameters
        
        Args:
            satellite_id (str): Unique identifier for the satellite
        """
        self.id = satellite_id
        self.uuid = str(uuid.uuid4())
        
        # Geographic coordinates (random placeholder values for now)
        self._coordinates = {
            'latitude': random.uniform(-90, 90),
            'longitude': random.uniform(-180, 180),
            'altitude': random.uniform(500, 1000)  # km
        }
        
        # Initialize metadata with default values
        self._metadata = SatelliteMetadata(
            computational_capacity=random.uniform(1000, 2000),  # 1000-2000 MIPS
            bandwidth_capacity=random.uniform(100, 1000),       # 100-1000 Mbps
            processing_power=random.uniform(1.0, 4.0),          # 1-4 GHz
            communication_range=random.uniform(1000, 2000),     # 1000-2000 km
            
            # Performance Metrics
            packet_loss_rate=random.uniform(0, 0.1),           # 0-10% loss
            transmission_delay=random.uniform(10, 100),         # 10-100 ms
            buffer_size=random.choice([512, 1024, 2048]),      # Common buffer sizes
            queue_capacity=random.randint(500, 2000),          # Packet queue size
            
            # Communication Parameters
            max_bandwidth_utilization=random.uniform(0.6, 0.9),
            min_signal_strength=random.uniform(-100, -80),
            frequency_band=random.choice(["Ka", "Ku", "X"]),
            modulation_scheme=random.choice(["BPSK", "QPSK", "8PSK"])
        )
        
        # Network-related attributes
        self.neighbors: Dict[str, Dict] = {}  # neighbor_id: {link_quality, start_time, end_time}
        self.active_links: Dict[str, Dict] = {}  # link_id: {satellite_id, start_time, end_time, link_quality}
        self.routing_table: Dict[str, Dict] = {}  # Routing information
        
    @property
    def coordinates(self) -> Dict[str, float]:
        """Get satellite coordinates"""
        return self._coordinates
    
    @coordinates.setter
    def coordinates(self, new_coordinates: Dict[str, float]):
        """Update satellite coordinates"""
        required_keys = {'latitude', 'longitude', 'altitude'}
        if not all(key in new_coordinates for key in required_keys):
            raise ValueError(f"Coordinates must contain all required keys: {required_keys}")
        self._coordinates = new_coordinates
    
    @property
    def metadata(self) -> SatelliteMetadata:
        """Get satellite metadata"""
        return self._metadata
    
    def update_metadata(self, **kwargs):
        """Update satellite metadata parameters"""
        for key, value in kwargs.items():
            if hasattr(self._metadata, key):
                setattr(self._metadata, key, value)
            else:
                raise ValueError(f"Invalid metadata parameter: {key}")
    
    def add_neighbor(self, neighbor_id: str, start_time: datetime, end_time: datetime, link_quality: float = 1.0):
        """
        Add or update a neighboring satellite with connection duration
        
        Args:
            neighbor_id (str): ID of the neighboring satellite
            start_time (datetime): Start time of the connection
            end_time (datetime): End time of the connection
            link_quality (float): Quality of the connection (default: 1.0)
        """
        self.neighbors[neighbor_id] = {
            'link_quality': link_quality,
            'start_time': start_time,
            'end_time': end_time
        }
        
        # Add to active links with a unique identifier
        link_id = f"{self.id}-{neighbor_id}"
        self.active_links[link_id] = {
            'satellite_id': neighbor_id,
            'start_time': start_time,
            'end_time': end_time,
            'link_quality': link_quality
        }
    
    def remove_neighbor(self, neighbor_id: str):
        """Remove a neighboring satellite"""
        self.neighbors.pop(neighbor_id, None)
        
    def update_link_quality(self, neighbor_id: str, link_quality: float):
        """Update the link quality with a neighboring satellite"""
        if neighbor_id in self.neighbors:
            self.neighbors[neighbor_id] = link_quality
            
    def get_active_links(self, current_time: Optional[datetime] = None) -> Dict[str, Dict]:
        """
        Get list of active communication links at the specified time
        
        Args:
            current_time (datetime, optional): Time to check for active links
                                            If None, returns all links
        
        Returns:
            Dict of active links with their details
        """
        if current_time is None:
            return self.active_links
            
        active = {}
        for link_id, link_info in self.active_links.items():
            if link_info['start_time'] <= current_time <= link_info['end_time']:
                active[link_id] = link_info
        return active
    
    def get_link_duration(self, neighbor_id: str) -> Optional[float]:
        """
        Get the duration of the link with a neighbor in seconds
        
        Args:
            neighbor_id (str): ID of the neighboring satellite
            
        Returns:
            float: Duration in seconds or None if neighbor not found
        """
        if neighbor_id in self.neighbors:
            neighbor = self.neighbors[neighbor_id]
            duration = (neighbor['end_time'] - neighbor['start_time']).total_seconds()
            return duration
        return None
    
    def update_routing_table(self, destination: str, next_hop: str, cost: float):
        """Update routing table entry"""
        self.routing_table[destination] = {
            'next_hop': next_hop,
            'cost': cost
        }
        
    def __str__(self) -> str:
        """String representation of the satellite"""
        return (f"Satellite {self.id}\n"
                f"Position: {self.coordinates}\n"
                f"Active neighbors: {len(self.neighbors)}\n"
                f"Computational capacity: {self.metadata.computational_capacity} MIPS\n"
                f"Bandwidth capacity: {self.metadata.bandwidth_capacity} Mbps\n"
                f"Current throughput: {self.metadata.calculate_throughput():.2f} Mbps\n"
                f"Transmission success rate: {self.metadata.successful_transmission_rate:.2%}\n"
                f"Frequency band: {self.metadata.frequency_band}\n"
                f"Modulation: {self.metadata.modulation_scheme}")

class SatelliteNetwork:
    def __init__(self):
        """Initialize satellite network"""
        self.satellites: Dict[str, Satellite] = {}
        
    def add_satellite(self, satellite_id: str) -> Satellite:
        """Add a new satellite to the network"""
        satellite = Satellite(satellite_id)
        self.satellites[satellite_id] = satellite
        return satellite
    
    def remove_satellite(self, satellite_id: str):
        """Remove a satellite from the network"""
        if satellite_id in self.satellites:
            # Remove satellite from neighbors' lists
            for sat in self.satellites.values():
                sat.remove_neighbor(satellite_id)
            # Remove satellite from network
            del self.satellites[satellite_id]
            
    def get_satellite(self, satellite_id: str) -> Optional[Satellite]:
        """Get a satellite by its ID"""
        return self.satellites.get(satellite_id)
    
    def get_all_satellites(self) -> Dict[str, Satellite]:
        """Get all satellites in the network"""
        return self.satellites

class RoutingEngine:
    def __init__(self, satellite: 'Satellite'):
        self.satellite = satellite
        self.routes: Dict[str, RouteInfo] = {}
        self.sequence_num = 0
        self.last_update = datetime.now()
        self.update_interval = timedelta(seconds=30)  # Configurable
        self.seen_updates: Set[tuple] = set()  # Track processed updates
        
    def process_periodic_update(self, current_time: datetime):
        """Periodic routing table update"""
        if current_time - self.last_update >= self.update_interval:
            self.update_routes()
            self.propagate_routes()
            self.last_update = current_time
    
    def update_routes(self):
        """Update routing table based on current network state"""
        # Update direct neighbor routes
        active_links = self.satellite.get_active_links()
        for link_id, link_info in active_links.items():
            neighbor_id = link_info['satellite_id']
            cost = 1.0 / link_info['link_quality']  # Higher link quality = lower cost
            
            self.routes[neighbor_id] = RouteInfo(
                destination=neighbor_id,
                next_hop=neighbor_id,
                cost=cost,
                timestamp=datetime.now(),
                valid_until=link_info['end_time'],
                sequence_num=self.sequence_num
            )
    
    def propagate_routes(self):
        """Create and send routing updates to neighbors"""
        self.sequence_num += 1
        update = RoutingUpdate(self.satellite.id, self.sequence_num)
        
        # Add current routes to update
        for route in self.routes.values():
            if datetime.now() <= route.valid_until:
                update.routes[route.destination] = route
        
        # Send to all active neighbors
        self._send_update_to_neighbors(update)
    
    def process_received_update(self, update: RoutingUpdate):
        """Process routing update received from neighbor"""
        # Check if we've seen this update before
        update_key = (update.sender_id, update.sequence_num)
        if update_key in self.seen_updates:
            return
        self.seen_updates.add(update_key)
        
        # Process each route in the update
        for destination, route in update.routes.items():
            # Skip if route is expired
            if datetime.now() > route.valid_until:
                continue
                
            # Calculate new cost through this neighbor
            new_cost = route.cost + self.get_link_cost(update.sender_id)
            
            # Update if we don't have a route or this is better
            if (destination not in self.routes or 
                new_cost < self.routes[destination].cost):
                self.routes[destination] = RouteInfo(
                    destination=destination,
                    next_hop=update.sender_id,
                    cost=new_cost,
                    timestamp=datetime.now(),
                    valid_until=route.valid_until,
                    sequence_num=self.sequence_num
                )
    
    def get_link_cost(self, neighbor_id: str) -> float:
        """Calculate cost of link to neighbor"""
        if neighbor_id in self.satellite.neighbors:
            return 1.0 / self.satellite.neighbors[neighbor_id]['link_quality']
        return float('inf')
    
    def _send_update_to_neighbors(self, update: RoutingUpdate):
        """Send routing update to all active neighbors"""
        # This would interface with the actual communication system
        # For now, we'll just print for demonstration
        active_links = self.satellite.get_active_links()
        for link_id, link_info in active_links.items():
            neighbor_id = link_info['satellite_id']
            print(f"Sending update from {self.satellite.id} to {neighbor_id}")

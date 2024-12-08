from threading import Thread, Lock
from queue import Queue
from dataclasses import dataclass
from typing import Dict, Set, Optional, List, Any
from datetime import datetime, timedelta
import time
import logging
import random

# Global satellite registry to store all satellites, and identify them uniquely
_satellite_registry: Dict[str, 'SatelliteThread'] = {}

def get_satellite_by_id(satellite_id: str) -> Optional['SatelliteThread']:
    """Get a satellite instance by its ID"""
    return _satellite_registry.get(satellite_id)

def register_satellite(satellite: 'SatelliteThread'):
    """Register a satellite in the global registry"""
    _satellite_registry[satellite.id] = satellite

def unregister_satellite(satellite_id: str):
    """Remove a satellite from the global registry"""
    _satellite_registry.pop(satellite_id, None)

@dataclass
class SatelliteMetadata:
    """Metadata class to store satellite capabilities and parameters"""
    # Basic Capabilities
    computational_capacity: float  # MIPS
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
    # min_signal_strength: float = -90.0      # dBm
    # frequency_band: str = "Ka"              # Default Ka band
    # modulation_scheme: str = "QPSK"         # Default modulation
    
    # Performance Tracking, will have to implment this per destination
    total_packets_sent: int = 0
    total_packets_received: int = 0
    successful_transmission_rate: float = 1.0  # Percentage (0-1)

@dataclass
class RoutingMessage:
    """Message structure for routing updates"""
    sender_id: str
    sequence_num: int
    routes: Dict[str, Dict]  # destination -> {'hops': count, 'cost': value}
    timestamp: datetime

@dataclass
class NeighborInfo:
    """Information about a neighboring satellite"""
    link_quality: float
    start_time: datetime
    end_time: datetime
    last_seen: datetime
    signal_strength: float
    bandwidth_available: float
    active: bool = True

class SatelliteThread(Thread):
    def __init__(self, satellite_id: str, k_hops: int = 2, clock=None):
        super().__init__()
        self.id = satellite_id
        register_satellite(self)
        self.k_hops = k_hops
        self.daemon = True
        self.clock = clock or datetime.now  # Use simulation clock if provided, else real time
        
        # Initialize metadata with random values (for simulation)
        self._metadata = SatelliteMetadata(
            computational_capacity=random.uniform(1000, 2000),
            bandwidth_capacity=random.uniform(100, 1000),
            processing_power=random.uniform(1.0, 4.0),
            communication_range=random.uniform(1000, 2000)
        )
        
        # Geographic coordinates
        self._coordinates = {
            'latitude': random.uniform(-90, 90),
            'longitude': random.uniform(-180, 180),
            'altitude': random.uniform(500, 1000)
        }
        
        # Communication queues
        self.incoming_queue = Queue()
        self.ground_queue = Queue()
        self.neighbor_update_queue = Queue()  # For neighbor updates
        
        # Routing information
        self.routing_table: Dict[str, Dict] = {}  # dest -> {next_hop, hops, cost, timestamp}
        self.sequence_num = 0
        self.seen_messages: Set[tuple] = set()
        
        # Locks
        self.routing_lock = Lock()
        self.neighbor_lock = Lock()
        self.metadata_lock = Lock()
        
        # Neighbor management
        self.neighbors: Dict[str, NeighborInfo] = {}
        self.neighbor_check_interval = 10  # seconds
        self.last_neighbor_check = datetime.now()
        
        # Update intervals
        self.routing_update_interval = 30  # seconds
        self.last_routing_update = datetime.now()
        
        # Performance tracking
        self.stats = {
            'messages_processed': 0,
            'routing_updates_sent': 0,
            'failed_transmissions': 0
        }
    
    @property
    def metadata(self) -> SatelliteMetadata:
        """Get satellite metadata"""
        with self.metadata_lock:
            return self._metadata
    
    def update_metadata(self, **kwargs):
        """Update satellite metadata parameters"""
        with self.metadata_lock:
            for key, value in kwargs.items():
                if hasattr(self._metadata, key):
                    setattr(self._metadata, key, value)
                else:
                    raise ValueError(f"Invalid metadata parameter: {key}")
    
    def add_neighbor(self, neighbor_id: str, start_time: datetime, 
                    end_time: datetime, link_quality: float = 0.9):
        """Add or update a neighboring satellite"""
        with self.neighbor_lock:
            self.neighbors[neighbor_id] = NeighborInfo(
                link_quality=link_quality,
                start_time=start_time,
                end_time=end_time,
                last_seen=self.clock.now(),  # Use simulation clock
                signal_strength=random.uniform(-85, -70),
                bandwidth_available=random.uniform(50, 100)
            )
            logging.info(f"{self.id}: Added neighbor {neighbor_id}")
            
            # Add direct route to the neighbor
            with self.routing_lock:
                self.routing_table[neighbor_id] = {
                    'next_hop': neighbor_id,
                    'hops': 1,
                    'cost': 1.0 / link_quality,
                    'timestamp': self.clock.now()
                }
            
            # Trigger routing update
            self.send_routing_update()
    
    def remove_neighbor(self, neighbor_id: str):
        """Remove a neighboring satellite"""
        with self.neighbor_lock:
            if neighbor_id in self.neighbors:
                del self.neighbors[neighbor_id]
                # Clean up routing entries through this neighbor
                self.cleanup_routes(neighbor_id)
                logging.info(f"Satellite {self.id} removed neighbor {neighbor_id}")
    
    def cleanup_routes(self, neighbor_id: str):
        """Clean up routing table entries going through a removed neighbor"""
        ## TODO Edge cases remain still, some of the destinations might still be reachable
        with self.routing_lock:
            routes_to_remove = []
            for dest, route_info in self.routing_table.items():
                if route_info['next_hop'] == neighbor_id:
                    routes_to_remove.append(dest)
            
            for dest in routes_to_remove:
                del self.routing_table[dest]
    
    def check_neighbor_status(self):
        """Check and update neighbor status"""
        current_time = datetime.now()
        with self.neighbor_lock:
            neighbors_to_remove = []
            for neighbor_id, info in self.neighbors.items():
                # Check if link is expired
                if current_time > info.end_time:
                    neighbors_to_remove.append(neighbor_id)
                    continue
                
                # Check if neighbor is still active
                if (current_time - info.last_seen).seconds > self.neighbor_check_interval * 2:
                    info.active = False
                    logging.warning(f"Neighbor {neighbor_id} appears to be inactive")
            
            # Remove expired neighbors
            for neighbor_id in neighbors_to_remove:
                self.remove_neighbor(neighbor_id)
    
    def run(self):
        """Main thread loop"""
        logging.info(f"Satellite {self.id} started")
        
        while True:
            current_time = self.clock.now()  # Use simulation time
            
            # Process incoming messages
            self.process_incoming_messages()
            
            # Process ground commands
            self.process_ground_commands()
            
            # Process neighbor updates
            self.process_neighbor_updates()
            
            # Periodic neighbor status check
            if (current_time - self.last_neighbor_check).seconds >= self.neighbor_check_interval:
                self.check_neighbor_status()
                self.last_neighbor_check = current_time
            
            # Periodic routing update
            if (current_time - self.last_routing_update).seconds >= self.routing_update_interval:
                self.send_routing_update()
                self.last_routing_update = current_time
            
            time.sleep(0.1)  # Still need this for real-time simulation control

    def process_neighbor_updates(self):
        """Process updates in the neighbor update queue"""
        while not self.neighbor_update_queue.empty():
            update = self.neighbor_update_queue.get()
            update_type = update.get('type', '')
            
            if update_type == 'ADD':
                self.add_neighbor(
                    neighbor_id=update['neighbor_id'],
                    start_time=update['start_time'],
                    end_time=update['end_time'],
                    link_quality=update.get('link_quality', 0.9)
                )
                self.print_routing_table(f"Added neighbor {update['neighbor_id']}")
                # Trigger immediate routing update when new neighbor is added
                self.send_routing_update()
                
            elif update_type == 'REMOVE':
                self.remove_neighbor(update['neighbor_id'])
                self.print_routing_table(f"Removed neighbor {update['neighbor_id']}")
                
            elif update_type == 'UPDATE':
                self.update_neighbor_status(
                    neighbor_id=update['neighbor_id'],
                    link_quality=update.get('link_quality'),
                    signal_strength=update.get('signal_strength'),
                    bandwidth_available=update.get('bandwidth_available')
                )
                self.print_routing_table(f"Updated neighbor {update['neighbor_id']} status")
    
    def update_neighbor_status(self, neighbor_id: str, **kwargs):
        """Update neighbor status information"""
        with self.neighbor_lock:
            if neighbor_id in self.neighbors:
                neighbor = self.neighbors[neighbor_id]
                for key, value in kwargs.items():
                    if value is not None and hasattr(neighbor, key):
                        setattr(neighbor, key, value)
                neighbor.last_seen = datetime.now()
                neighbor.active = True
    
    def process_incoming_messages(self):
        """Process messages from other satellites"""
        while not self.incoming_queue.empty():
            message = self.incoming_queue.get()
            
            if isinstance(message, RoutingMessage):
                self.process_routing_message(message)
                self.stats['messages_processed'] += 1
    
    def process_routing_message(self, message: RoutingMessage):
        """Process a routing update message"""
        # Check if we've seen this message before
        message_key = (message.sender_id, message.sequence_num)
        if message_key in self.seen_messages:
            return
        self.seen_messages.add(message_key)
        
        # Update neighbor's last_seen timestamp
        self.update_neighbor_status(message.sender_id)
        
        routes_updated = False
        with self.routing_lock:
            # First, update direct route to the sender (1 hop)
            if message.sender_id not in self.routing_table:
                self.routing_table[message.sender_id] = {
                    'next_hop': message.sender_id,
                    'hops': 1,
                    'cost': self.get_link_cost(message.sender_id),
                    'timestamp': self.clock.now()  # Use simulation clock
                }
                routes_updated = True
                logging.info(f"{self.id}: Added direct route to {message.sender_id}")
            
            # Process routes advertised by sender
            for dest, route_info in message.routes.items():
                if dest == self.id:  # Skip routes to self
                    continue
                
                # Calculate new hop count through this neighbor
                new_hops = route_info['hops'] + 1
                
                # Only consider routes within k_hops limit
                if new_hops > self.k_hops:
                    continue
                
                # Calculate new cost
                new_cost = route_info['cost'] + self.get_link_cost(message.sender_id)
                
                current_route = self.routing_table.get(dest)
                current_time = self.clock.now()
                
                should_update = (
                    not current_route or
                    new_hops < current_route['hops'] or
                    (new_hops == current_route['hops'] and new_cost < current_route['cost']) or
                    (current_time - current_route['timestamp']) > timedelta(minutes=5)
                )
                
                if should_update:
                    self.routing_table[dest] = {
                        'next_hop': message.sender_id,
                        'hops': new_hops,
                        'cost': new_cost,
                        'timestamp': current_time
                    }
                    routes_updated = True
                    logging.info(f"{self.id}: Updated route to {dest} via {message.sender_id}")
        
        if routes_updated:
            self.print_routing_table(f"Updated by message from {message.sender_id}")
            self.send_routing_update()
    
    def send_routing_update(self):
        """Send routing updates to neighbors"""
        self.sequence_num += 1
        current_time = datetime.now()
        
        with self.routing_lock:
            routes = {}
            
            # Include all valid routes within k_hops
            for dest, route in self.routing_table.items():
                # Only advertise fresh routes within k_hops - 1
                # (since neighbor will add 1 hop)
                if (route['hops'] < self.k_hops and 
                    (current_time - route['timestamp']) <= timedelta(minutes=5)):
                    routes[dest] = {
                        'hops': route['hops'],
                        'cost': route['cost']
                    }
        
        message = RoutingMessage(
            sender_id=self.id,
            sequence_num=self.sequence_num,
            routes=routes,
            timestamp=current_time
        )
        
        self.broadcast_to_neighbors(message)
        self.stats['routing_updates_sent'] += 1
        self.print_routing_table("Periodic update")
    
    def get_link_cost(self, neighbor_id: str) -> float:
        """Calculate cost of link to neighbor based on multiple factors"""
        with self.neighbor_lock:
            if neighbor_id in self.neighbors and self.neighbors[neighbor_id].active:
                neighbor = self.neighbors[neighbor_id]
                
                # Combine multiple factors for link cost
                quality_factor = 1.0 / neighbor.link_quality
                signal_factor = abs(neighbor.signal_strength) / 100.0
                bandwidth_factor = 1.0 / (neighbor.bandwidth_available + 1)
                
                # Weighted combination of factors
                cost = (0.5 * quality_factor + 
                       0.3 * signal_factor + 
                       0.2 * bandwidth_factor)
                
                return max(1.0, cost)  # Minimum cost of 1.0
        return float('inf')
    
    def broadcast_to_neighbors(self, message: Any):
        """Send message to all active neighbors"""
        with self.neighbor_lock:
            current_time = datetime.now()
            for neighbor_id, info in self.neighbors.items():
                if (info.active and 
                    info.start_time <= current_time <= info.end_time):
                    # In a real implementation, this would use actual network communication
                    # For now, we'll assume there's a way to get the neighbor's queue
                    neighbor = get_satellite_by_id(neighbor_id)  # This function needs to be implemented
                    if neighbor:
                        neighbor.incoming_queue.put(message)
    
    def print_routing_table(self, reason: str = ""):
        """Print current routing table with detailed information"""
        with self.routing_lock:
            logging.info(f"\n=== Routing Table for {self.id} ===")
            if reason:
                logging.info(f"Update reason: {reason}")
            logging.info(f"Current time: {datetime.now()}")
            logging.info(f"Number of routes: {len(self.routing_table)}")
            
            # Sort routes by hop count for better readability
            sorted_routes = sorted(
                self.routing_table.items(), 
                key=lambda x: (x[1]['hops'], x[1]['cost'])
            )
            
            for dest, route in sorted_routes:
                age = (datetime.now() - route['timestamp']).seconds
                logging.info(
                    f"To: {dest:8} | "
                    f"Via: {route['next_hop']:8} | "
                    f"Hops: {route['hops']:2} | "
                    f"Cost: {route['cost']:6.2f} | "
                    f"Age: {age:3}s"
                )
            logging.info("=" * 50)

    def process_ground_commands(self):
        """Process commands from ground station"""
        pass  # Ignoring ground commands for now

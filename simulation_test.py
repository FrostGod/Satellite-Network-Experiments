from datetime import datetime, timedelta
import time
import logging
from connection_parse import parse_link_topology
from satellites import SatelliteThread, register_satellite, get_satellite_by_id
import random
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(message)s',
    datefmt='%H:%M:%S'
)

class SimulationClock:
    def __init__(self, start_time: datetime):
        self.start_time = start_time
        self.current_time = start_time
        
    def now(self) -> datetime:
        return self.current_time
    
    def advance(self, seconds: int):
        self.current_time += timedelta(seconds=seconds)

def adjust_topology_times(topology: List[Dict]) -> List[Dict]:
    """Adjust topology times to current time"""
    if not topology:
        return topology
        
    # Calculate time difference between now and first link start
    time_diff = datetime.now() - topology[0]['start_time']
    
    # Adjust all times
    for link in topology:
        link['start_time'] += time_diff
        link['end_time'] += time_diff
    
    return topology

def create_test_topology():
    """Create a simplified test topology for validation"""
    # Using a 10-minute window for easier testing
    base_time = datetime(2024, 1, 1, 12, 0, 0)  # 2024-01-01 12:00:00
    
    test_topology = [
        # Ring topology: 1->2->3->4->5->1
        {
            'source': 'LEO_1 +X_OCT',
            'destination': 'LEO_2 -X_OCT',
            'start_time': base_time,
            'end_time': base_time + timedelta(minutes=10),
            'link_type': 'LEO_LEO'
        },
        {
            'source': 'LEO_2 +X_OCT',
            'destination': 'LEO_3 -X_OCT',
            'start_time': base_time,
            'end_time': base_time + timedelta(minutes=10),
            'link_type': 'LEO_LEO'
        },
        {
            'source': 'LEO_3 +X_OCT',
            'destination': 'LEO_4 -X_OCT',
            'start_time': base_time,
            'end_time': base_time + timedelta(minutes=10),
            'link_type': 'LEO_LEO'
        },
        {
            'source': 'LEO_4 +X_OCT',
            'destination': 'LEO_5 -X_OCT',
            'start_time': base_time,
            'end_time': base_time + timedelta(minutes=10),
            'link_type': 'LEO_LEO'
        },
        {
            'source': 'LEO_5 +X_OCT',
            'destination': 'LEO_1 -X_OCT',
            'start_time': base_time,
            'end_time': base_time + timedelta(minutes=10),
            'link_type': 'LEO_LEO'
        },
        
        # Cross links that appear later
        {
            'source': 'LEO_1 +Y_OCT',
            'destination': 'LEO_3 -Y_OCT',
            'start_time': base_time + timedelta(minutes=2),
            'end_time': base_time + timedelta(minutes=8),
            'link_type': 'LEO_LEO'
        },
        {
            'source': 'LEO_2 +Y_OCT',
            'destination': 'LEO_4 -Y_OCT',
            'start_time': base_time + timedelta(minutes=3),
            'end_time': base_time + timedelta(minutes=7),
            'link_type': 'LEO_LEO'
        }
    ]
    
    return test_topology

def setup_test_network():
    """Create and setup test network using simplified topology"""
    # Use test topology instead of reading from file
    topology = create_test_topology()
    # later uncomment it
    # topology = parse_link_topology('Link Topology Table.csv')
    
    # Get simulation start time from the first link
    sim_start_time = topology[0]['start_time']
    sim_clock = SimulationClock(sim_start_time)
    
    # Extract unique satellites
    satellites = set()
    for link in topology:
        if link['link_type'] == 'LEO_LEO':
            satellites.add(link['source'].split(' ')[0])
            satellites.add(link['destination'].split(' ')[0])
    
    # Create satellite threads with simulation clock
    satellite_threads = []
    for sat_id in satellites:
        satellite = SatelliteThread(sat_id, k_hops=2, clock=sim_clock)
        satellite_threads.append(satellite)
        logging.info(f"Created satellite: {sat_id}")
    
    # Start all satellites
    for satellite in satellite_threads:
        satellite.start()
    
    # Wait for initialization
    time.sleep(1)
    
    # Add initial connections based on topology
    for link in topology:
        if link['link_type'] == 'LEO_LEO':
            source_id = link['source'].split(' ')[0]
            dest_id = link['destination'].split(' ')[0]
            
            source_sat = get_satellite_by_id(source_id)
            if source_sat:
                update = {
                    'type': 'ADD',
                    'neighbor_id': dest_id,
                    'start_time': link['start_time'],
                    'end_time': link['end_time'],
                    'link_quality': random.uniform(0.7, 1.0)
                }
                source_sat.neighbor_update_queue.put(update)
    
    return satellite_threads, sim_clock

def run_simulation_step(satellites, sim_clock, step_seconds=30):
    """Run one step of the simulation"""
    sim_clock.advance(step_seconds)
    
    # Let all satellites process their queues
    time.sleep(0.5)
    
    # Print routing tables for all satellites
    for sat in satellites:
        sat.print_routing_table("Simulation step update")

def test_routing_updates():
    """Test routing updates between satellites"""
    satellites, sim_clock = setup_test_network()
    
    # Run simulation for a few steps
    logging.info("\nRunning simulation steps...")
    for _ in range(6):  # Run for 3 minutes of simulation time
        run_simulation_step(satellites, sim_clock)
    
    # Test specific route
    if len(satellites) >= 2:
        sat1 = satellites[0]
        sat2 = satellites[-1]
        logging.info(f"\nChecking route from {sat1.id} to {sat2.id}")
        with sat1.routing_lock:
            if sat2.id in sat1.routing_table:
                route = sat1.routing_table[sat2.id]
                path = []
                current = sat1.id
                while current != sat2.id:
                    path.append(current)
                    current = sat1.routing_table[current]['next_hop']
                path.append(sat2.id)
                logging.info(
                    f"Route found: {' -> '.join(path)} "
                    f"(hops: {route['hops']}, cost: {route['cost']:.2f})"
                )
            else:
                logging.info(f"No route found from {sat1.id} to {sat2.id}")
    
    return satellites, sim_clock

def test_link_changes():
    """Test network adaptation to link changes"""
    # Fix: Capture both return values from test_routing_updates()
    satellites, sim_clock = test_routing_updates()  # Unpack both values
    
    logging.info("\nSimulating link quality changes...")
    # Simulate link quality changes
    for satellite in satellites[:3]:
        for neighbor_id in list(satellite.neighbors.keys())[:2]:
            update = {
                'type': 'UPDATE',
                'neighbor_id': neighbor_id,
                'link_quality': random.uniform(0.3, 0.6)  # Degrade link quality
            }
            satellite.neighbor_update_queue.put(update)
            logging.info(f"Degraded link quality between {satellite.id} and {neighbor_id}")
    
    # Let the network adapt
    logging.info("\nLetting network adapt to changes...")
    time.sleep(5)

def main():
    """Main test function"""
    logging.info("Starting satellite network simulation")
    
    # Test 1: Basic routing updates
    logging.info("\n=== Testing basic routing updates ===")
    test_routing_updates()
    
    # Test 2: Link changes
    logging.info("\n=== Testing network adaptation to link changes ===")
    test_link_changes()
    
    logging.info("\nSimulation complete")

if __name__ == "__main__":
    main() 
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
    topology = create_test_topology()
    sim_start_time = topology[0]['start_time']
    sim_clock = SimulationClock(sim_start_time)
    
    # Create satellite threads
    satellite_threads = []
    satellites = set()
    for link in topology:
        satellites.add(link['source'].split(' ')[0])
        satellites.add(link['destination'].split(' ')[0])
    
    for sat_id in sorted(satellites):  # Sort for consistent ordering
        satellite = SatelliteThread(sat_id, k_hops=2, clock=sim_clock)
        satellite_threads.append(satellite)
        logging.info(f"Created satellite: {sat_id}")
    
    # Start all satellites
    for satellite in satellite_threads:
        satellite.start()
        logging.info(f"Started satellite: {satellite.id}")
    
    # Wait for thread initialization
    time.sleep(2)
    logging.info("All satellites initialized")
    
    # Add initial connections (bidirectional)
    for link in topology:
        source_id = link['source'].split(' ')[0]
        dest_id = link['destination'].split(' ')[0]
        
        # Forward direction
        source_sat = get_satellite_by_id(source_id)
        if source_sat:
            update = {
                'type': 'ADD',
                'neighbor_id': dest_id,
                'start_time': link['start_time'],
                'end_time': link['end_time']
            }
            source_sat.neighbor_update_queue.put(update)
            logging.info(f"Added forward link: {source_id} -> {dest_id}")
        
        # Reverse direction
        dest_sat = get_satellite_by_id(dest_id)
        if dest_sat:
            update = {
                'type': 'ADD',
                'neighbor_id': source_id,
                'start_time': link['start_time'],
                'end_time': link['end_time']
            }
            dest_sat.neighbor_update_queue.put(update)
            logging.info(f"Added reverse link: {dest_id} -> {source_id}")
    
    # After adding initial connections, trigger routing updates
    for satellite in satellite_threads:
        satellite.send_routing_update()
        logging.info(f"Triggered initial routing update for {satellite.id}")
    
    # Wait for initial routing updates
    time.sleep(3)
    logging.info("Initial connections established")
    
    return satellite_threads, sim_clock

def wait_for_route_convergence(satellites, timeout=10):
    """Wait for routing tables to converge or timeout"""
    start_time = time.time()
    prev_routes = {}
    stable_count = 0
    
    while time.time() - start_time < timeout:
        current_routes = {}
        
        # Collect current routing tables
        for sat in satellites:
            with sat.routing_lock:
                current_routes[sat.id] = {
                    dest: info['hops'] 
                    for dest, info in sat.routing_table.items()
                }
        
        # Check if routes have changed
        if prev_routes == current_routes:
            stable_count += 1
            if stable_count >= 2:  # Reduced from 3 to 2 consecutive checks
                logging.info("Routing tables have converged")
                return True
        else:
            stable_count = 0
            
        prev_routes = current_routes.copy()
        time.sleep(0.5)  # Reduced sleep time
    
    logging.error("Timeout waiting for route convergence")
    return False

def verify_routes(satellite, expected_routes):
    """
    Verify that a satellite's routing table matches the expected routes
    
    Args:
        satellite: SatelliteThread instance
        expected_routes: dict of expected routes in format {dest: {'next_hop': str, 'hops': int}}
    
    Returns:
        bool: True if routes match expectations
    """
    with satellite.routing_lock:
        # Check if all expected routes exist
        for dest, expected in expected_routes.items():
            if dest not in satellite.routing_table:
                return False
            actual = satellite.routing_table[dest]
            if actual['next_hop'] != expected['next_hop'] or actual['hops'] != expected['hops']:
                return False
        
        # Check if there are no unexpected routes
        return len(satellite.routing_table) == len(expected_routes)

def test_routing_updates():
    """Test routing updates between satellites"""
    satellites, sim_clock = setup_test_network()
    
    # Initial wait for setup
    logging.info("Waiting for initial setup...")
    time.sleep(2)
    
    # Multiple rounds of routing updates with state logging
    for round in range(1, 6):  # 5 rounds should be enough for full convergence
        logging.info(f"\n=== Round {round} of Routing Updates ===")
        
        # Trigger routing updates for all satellites with a small delay between each
        for sat in satellites:
            sat.send_routing_update()
            logging.info(f"Triggered routing update for {sat.id}")
            time.sleep(0.1)  # Small delay between satellites
            print("DIVI 2")
        
        # Wait a shorter time between rounds
        time.sleep(1)
        
        # Print current routing state
        logging.info(f"\nRouting State after Round {round}:")
        for sat in satellites:
            with sat.routing_lock:
                routes = {dest: {'next_hop': info['next_hop'], 'hops': info['hops']} 
                         for dest, info in sat.routing_table.items()}
                logging.info(f"{sat.id} routes: {routes}")
    
    # Final convergence check with shorter timeout
    logging.info("\nChecking final route convergence...")
    converged = wait_for_route_convergence(satellites, timeout=10)  # Reduced timeout
    
    if not converged:
        logging.error("Failed to achieve route convergence")
        return satellites, sim_clock
    
    # Verify final state
    leo1 = next(sat for sat in satellites if sat.id == "LEO_1")
    expected_routes_leo1 = {
        "LEO_2": {"next_hop": "LEO_2", "hops": 1},
        "LEO_3": {"next_hop": "LEO_2", "hops": 2},
        "LEO_5": {"next_hop": "LEO_5", "hops": 1},
        "LEO_4": {"next_hop": "LEO_5", "hops": 2}
    }
    
    # Print final state
    logging.info("\nFinal Routing State:")
    for sat in satellites:
        with sat.routing_lock:
            routes = {dest: {'next_hop': info['next_hop'], 'hops': info['hops']} 
                     for dest, info in sat.routing_table.items()}
            logging.info(f"{sat.id} final routes: {routes}")
    
    if verify_routes(leo1, expected_routes_leo1):
        logging.info("All expected routes verified for LEO_1")
    else:
        logging.error("Route verification failed for LEO_1")
        with leo1.routing_lock:
            actual_routes = {dest: info['hops'] for dest, info in leo1.routing_table.items()}
            logging.error(f"Actual routes: {actual_routes}")
            logging.error(f"Expected routes: {expected_routes_leo1}")
    
    return satellites, sim_clock

def test_link_changes():
    """Test network adaptation to link changes"""
    satellites, sim_clock = test_routing_updates()
    
    logging.info("\nSimulating link changes...")
    # Comment out link quality changes for now
    '''
    for satellite in satellites[:3]:
        for neighbor_id in list(satellite.neighbors.keys())[:2]:
            update = {
                'type': 'UPDATE',
                'neighbor_id': neighbor_id,
                'link_quality': random.uniform(0.3, 0.6)  # Degrade link quality
            }
            satellite.neighbor_update_queue.put(update)
            logging.info(f"Degraded link quality between {satellite.id} and {neighbor_id}")
    '''
    
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
    # logging.info("\n=== Testing network adaptation to link changes ===")
    # test_link_changes()
    
    logging.info("\nSimulation complete")

if __name__ == "__main__":
    main() 
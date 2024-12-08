from datetime import datetime, timedelta
import time
import logging
from connection_parse import parse_link_topology
from satellites import SatelliteThread, register_satellite, get_satellite_by_id
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(message)s',
    datefmt='%H:%M:%S'
)

def setup_test_network():
    """Create and setup test network from topology data"""
    print("DIVI")
    exit
    # Parse topology data
    topology = parse_link_topology('Link Topology Table.csv')
    
    # Extract unique satellites
    satellites = set()
    for link in topology:
        if link['link_type'] == 'LEO_LEO':
            satellites.add(link['source'].split(' ')[0])
            satellites.add(link['destination'].split(' ')[0])
    
    # Create satellite threads
    print(len(satellites))
    # exit
    satellite_threads = []
    for sat_id in satellites:
        satellite = SatelliteThread(sat_id, k_hops=2)
        satellite_threads.append(satellite)
        logging.info(f"Created satellite: {sat_id}")
    
    # Start all satellites
    for satellite in satellite_threads:
        satellite.start()
    
    # Wait for all satellites to initialize
    time.sleep(1)
    
    # Add initial connections based on topology
    for link in topology:
        if link['link_type'] == 'LEO_LEO':
            source_id = link['source'].split(' ')[0]
            dest_id = link['destination'].split(' ')[0]
            
            source_sat = get_satellite_by_id(source_id)
            if source_sat:
                # Add neighbor with the connection window
                update = {
                    'type': 'ADD',
                    'neighbor_id': dest_id,
                    'start_time': link['start_time'],
                    'end_time': link['end_time'],
                    'link_quality': random.uniform(0.7, 1.0)
                }
                source_sat.neighbor_update_queue.put(update)
    
    return satellite_threads

def test_routing_updates():
    """Test routing updates between satellites"""
    satellites = setup_test_network()
    
    # Let the network stabilize
    logging.info("\nLetting network stabilize for initial routing...")
    time.sleep(5)
    
    # No need to print routing tables here as they're now printed automatically
    
    # Test specific route
    if len(satellites) >= 2:
        sat1 = satellites[0]
        sat2 = satellites[-1]
        logging.info(f"\nChecking route from {sat1.id} to {sat2.id}")
        with sat1.routing_lock:
            if sat2.id in sat1.routing_table:
                route = sat1.routing_table[sat2.id]
                logging.info(
                    f"Route found: {sat1.id} -> {route['next_hop']} "
                    f"-> ... -> {sat2.id} (cost: {route['cost']:.2f})"
                )
            else:
                logging.info(f"No route found from {sat1.id} to {sat2.id}")
    
    return satellites

def test_link_changes():
    """Test network adaptation to link changes"""
    satellites = test_routing_updates()  # Reuse the network setup
    
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
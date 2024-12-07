from datetime import datetime, timedelta
from satellites import Satellite, SatelliteNetwork, RoutingEngine
from connection_parse import parse_link_topology
import time
from network_visualizer import create_visualizer

def create_test_network():
    """Create a test satellite network from the Link Topology data"""
    network = SatelliteNetwork()
    
    # Parse the link topology data
    topology = parse_link_topology('Link Topology Table.csv')

    print("DIVI ", topology) 
    
    # Extract unique satellites
    satellites = set()
    for link in topology:
        if link['link_type'] == 'LEO_LEO':
            satellites.add(link['source'].split(' ')[0])
            satellites.add(link['destination'].split(' ')[0])
    
    # Create satellites
    for sat_id in satellites:
        network.add_satellite(sat_id)
        print(f"Created satellite: {sat_id}")
    
    print(len(satellites))
    
    # Add connections between satellites
    for link in topology:
        if link['link_type'] == 'LEO_LEO':
            source_sat = network.get_satellite(link['source'].split(' ')[0])
            if source_sat:
                source_sat.add_neighbor(
                    neighbor_id=link['destination'].split(' ')[0],
                    start_time=link['start_time'],
                    end_time=link['end_time'],
                    link_quality=0.9  # Example link quality
                )
    
    return network

def run_routing_simulation(network: SatelliteNetwork, duration_minutes: int = 60):
    """Run a simulation of the routing protocol"""
    # Create routing engines for each satellite
    routing_engines = {}
    for sat_id, satellite in network.satellites.items():
        routing_engines[sat_id] = RoutingEngine(satellite)
    
    # Simulation time parameters
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    current_time = start_time
    
    print("\nStarting routing simulation...")
    print(f"Simulation period: {duration_minutes} minutes")
    
    # Simulation loop
    while current_time < end_time:
        # Process updates for each satellite
        for sat_id, engine in routing_engines.items():
            # Process periodic updates
            engine.process_periodic_update(current_time)
            
            # Print current routes
            print(f"\nRoutes for {sat_id} at {current_time}:")
            for dest, route in engine.routes.items():
                print(f"  To {dest}: via {route.next_hop} (cost: {route.cost:.2f})")
        
        # Advance simulation time
        current_time += timedelta(seconds=30)
        time.sleep(1)  # Slow down simulation for observation

def test_satellite_capabilities():
    """Test individual satellite capabilities"""
    print("\nTesting individual satellite capabilities...")
    
    # Create a test satellite
    sat = Satellite("TEST_SAT_1")
    
    # Print satellite information
    print(sat)
    
    # Test metadata updates
    sat.update_metadata(
        computational_capacity=1500,
        bandwidth_capacity=800,
        processing_power=2.5
    )
    
    print("\nAfter metadata update:")
    print(f"Computational Capacity: {sat.metadata.computational_capacity} MIPS")
    print(f"Bandwidth Capacity: {sat.metadata.bandwidth_capacity} Mbps")
    print(f"Processing Power: {sat.metadata.processing_power} GHz")

def main():
    """Main simulation function"""
    print("Starting Satellite Network Simulation\n")
    
    # Test 1: Individual Satellite Capabilities
    test_satellite_capabilities()
    
    # Test 2: Network Creation and Routing
    print("\nCreating satellite network...")
    network = create_test_network()
    
    print(f"\nNetwork created with {len(network.satellites)} satellites")
    
    # Create and run visualizer
    app, root = create_visualizer(network)
    
    # Start simulation in a separate thread
    import threading
    sim_thread = threading.Thread(
        target=lambda: run_routing_simulation(network, duration_minutes=5)
    )
    sim_thread.daemon = True
    sim_thread.start()
    
    # Run GUI
    root.mainloop()

if __name__ == "__main__":
    main() 
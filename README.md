# Satellite Network Communication System ( Space to Space )

## Overview
This project implements a distributed routing system for satellite-to-satellite communication in space. It simulates how satellites in orbit can form a dynamic mesh network and route messages between each other efficiently.

## Key Features
- **Dynamic Routing**: Satellites automatically discover routes to other satellites using a distance vector routing algorithm
- **Time-Based Links**: Satellite connections are time-dependent, simulating real orbital mechanics where satellites can only communicate when in range
- **Fault Tolerance**: The system handles link failures and satellite unavailability gracefully
- **Scalable Architecture**: Can handle multiple satellites joining and leaving the network

## How It Works

### 1. Satellite Network
- Each satellite runs as an independent thread
- Satellites maintain connections with neighbors that are within communication range
- Links between satellites have properties like:
  - Signal strength
  - Bandwidth capacity
  - Link quality
  - Active time windows

### 2. Routing Protocol
- Uses a modified distance vector routing protocol
- Each satellite maintains a routing table with:
  - Destination satellites
  - Next hop to reach each destination
  - Number of hops
  - Route cost
  - Route timestamp

### 3. Message Handling
- Satellites exchange routing updates periodically
- Messages are queued and processed asynchronously
- Failed transmissions are handled gracefully with retries

## Components

### Core Files
- `satellites.py`: Main satellite implementation with routing logic
- `simulation_test.py`: Test framework for simulating satellite networks
- `connection_parse.py`: Parses satellite connection topology data

### Data Structures
- `SatelliteThread`: Core satellite class that handles routing and communication
- `RoutingMessage`: Message format for routing updates
- `SatelliteMetadata`: Stores satellite capabilities and parameters
- `NeighborInfo`: Tracks information about neighboring satellites

## Future Improvements
- Add support for prioritized message routing
- Implement congestion control
- Add security features for communication
- Support for ground station communication
- More sophisticated link cost calculations

## Usage

### Running the Simulation
$python simulation_test.py



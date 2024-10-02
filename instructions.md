### Instructions for Satellite Network Simulator
1 - Take in the satellites input
2 - construct the grid with the satellites
3 - Given a Source Satellite and Target Sattelite, Compute the Shortest path from source to destination
4 - Given a Normal Satellite, Can we now figure out the closest Compute Satellite from it


## Satellite Input format
1 - Co-ordinates (For now X, Y)
2 - Satellite type (Compute Heavy Satellite (CS), Normal Satellite (NS))
3 - Direction of the Satellite (Example - Example East to West, North to South)
4 - Compute Capacity (Eg - RAM)

## Important points to note
1 - If they are in Same Y they are in same intra orbit
2 - If they are in Differnt Y they are in different orbits
3 - Intra Orbital length are always shorter than Inter orbit length
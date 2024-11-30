import csv
from datetime import datetime

def parse_link_topology(csv_file):
    """
    Parse Link Topology Table CSV file into a dictionary structure
    
    Args:
        csv_file (str): Path to the CSV file
        
    Returns:
        dict: Dictionary containing parsed link data
    """
    links = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert timestamps to datetime objects
            start_time = datetime.strptime(row['StartTime'], '%d-%b-%Y %H:%M:%S')
            end_time = datetime.strptime(row['EndTime'], '%d-%b-%Y %H:%M:%S')
            
            link = {
                'source': row['Source'],
                'destination': row['Target'], 
                'start_time': start_time,
                'end_time': end_time,
                'link_type': row['LinkType']
            }
            links.append(link)
            
    return links

def main():
    # Example usage
    csv_file = 'Link Topology Table.csv'
    topology = parse_link_topology(csv_file)
    
    # Print first few entries as example
    # for link in topology:
    #     print(f"Source: {link['source']}")
    #     print(f"Destination: {link['destination']}")
    #     print(f"Start Time: {link['start_time']}")
    #     print(f"End Time: {link['end_time']}")
    #     print(f"Link Type: {link['link_type']}")
    #     print("---")

    ## from the dict, we need to figure out how many satellites are there, and link type is LEO_LEO
    satellites = set()
    for link in topology:
        if link['link_type'] == 'LEO_LEO':
            satellites.add(link['source'].split(' ')[0])
            satellites.add(link['destination'].split(' ')[0])
    print(f"Number of Satellites: {len(satellites)}")
    print(satellites)

if __name__ == '__main__':
    main()
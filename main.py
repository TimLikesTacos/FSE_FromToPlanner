from src import assignment_planner, flightpath
import matplotlib.pyplot as plt

if __name__ == '__main__':

    # Flight from Portland, OR to JFK airport in New York, NY, not including water runways, with a 10nm left/right buffer
    fp = flightpath.FlightPath('kpdx', 'kjfk', 10, exclude='water')
    # Adds assignments to the flightpath
    fp.add_assignments()
    # Using values for a Cessna 172, weight capacity of 224 kg and 2 additional passenger capacity
    plan = assignment_planner.FromToPlanner(fp, 224, 2)
    print(f'{plan}')

    # Plot the flightpath with the airports that fall into the area
    fp.plot(plt, include_airports=True)
    plt.savefig('example.png')




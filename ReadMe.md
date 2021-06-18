## About
This program simulates a day-ahead market-clearing of an electricity market using Python.
It generates the market prices, the system costs, and the revenue of each agent in every
period.
## Requirements
To run this code, the installation of the used libraries is a prerequisite. It is recommended that the libraries are installed and the code is run through a virtual environment in order not to interfere with the system's libraries. Through the terminal, first check if virtualenv is installed by typing the following:

`sudo apt-get install python3-venv`

To create a virtual environment:

`python3 -m venv marketsim`

To activate the environment:

`source marketsim/bin/activate`

Finally the requirements can be installed using:

`pip install gekko`

##Running the Code
To run this code, first clone this repository then go to the directory of the cloned repository on your machine. Afterwards run:

`python run.py`
## Code Components
### Main
main.py retrieves the input data consisting of the demand and capacity of each agent in
every period. In market.add_agent add for each agent its ID, technology type, capacity, and
marginal cost. In addition, for storage units, add energy storage capacity.
### Market Run
market.run() will find the bidding price and the capacity of all agents.
market.run() performs the market-clearing without energy storage units and finds the
market prices. Next, it finds the optimal strategy for the energy storage facility to buy or sell
electricity with charging constraints modeled as a MINLP optimization problem.
### Output
The output consisting of market prices, the system costs, and the revenue of each agent
generated as a CSV file.

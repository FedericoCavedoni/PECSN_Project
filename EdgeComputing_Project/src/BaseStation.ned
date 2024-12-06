package edgecomputing_project;

simple BaseStation {
    parameters:        
        double delay;
        double serviceRate;

        int queueSize;

        int numBaseStations;
        
    gates:
        input in @directIn;
}
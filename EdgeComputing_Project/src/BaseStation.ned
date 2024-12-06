package edgecomputing_project;

simple BaseStation {
    parameters:        
        double delay;
        double serviceRate;

        int queueSize;   
    gates:
        input in @directIn;
}
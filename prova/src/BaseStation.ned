package edgecomputing_project;

simple BaseStation {
    parameters:        
        double delay;
        double serviceRate;
        
    gates:
        input in[];
        output out[];
}
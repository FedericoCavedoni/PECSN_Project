package edgecomputing_project;

simple BaseStation {
    parameters:        
        double delay;
        double serviceRate;

        int queueSize;   

        @signal[responseTimeSignal];
        @statistic[responseTime](source="responseTimeSignal"; record=mean,vector);
    gates:
        input in @directIn;
}
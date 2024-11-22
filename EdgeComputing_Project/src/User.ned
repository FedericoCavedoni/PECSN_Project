package edgecomputing_project;

simple User {
    parameters:
        double x;          
        double y;          
        
        double taskInterval; 
        double taskSize;     
        
        double intervalRate;
        double sizeRate;
  
    gates:
        output out;
}

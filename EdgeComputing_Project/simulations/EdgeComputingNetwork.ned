package edgecomputing_project.simulations;

import edgecomputing_project.BaseStation;
import edgecomputing_project.User;

network EdgeComputingNetwork {
    parameters:
        int numBaseStations; 
        int numUsers;        
        
        int width; 
        int height; 
        
    submodules:
        baseStations[numBaseStations]: BaseStation {
            @display("i=block/router");
        }
        users[numUsers]: User {
            @display("i=block/person");
        }
}

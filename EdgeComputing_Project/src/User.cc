#include "User.h"
#include "BaseStation.h"
#include <cmath>
#include <climits> // per INT_MAX

Define_Module(User);

void User::initialize() {
    intervalRate = par("intervalRate").doubleValue();  
    sizeRate = par("sizeRate").doubleValue();          

    if (par("uniformDistribution").boolValue()) {
        // Distribuzione uniforme
        cModule *parent = getParentModule();
        if (!parent) {
            EV << "[ERROR] Parent module not found during initialization.\n";
            endSimulation();
            return;
        }

        if (!parent->hasPar("width") || !parent->hasPar("height")) {
            EV << "[ERROR] Parent module missing 'width' or 'height' parameters.\n";
            endSimulation();
            return;
        }

        int width = parent->par("width").intValue();  
        int height = parent->par("height").intValue();  

        x = uniform(0, width, 0);
        y = uniform(0, height, 1);

        EV << "[DEBUG] User " << getIndex() << " positioned uniformly at (" << x << ", " << y << ")\n";
    }
    else {
        // Distribuzione lognormale
        double mean = par("mean").doubleValue();        
        double std_dev = par("std_dev").doubleValue();    

        if (mean <= 0 || std_dev <= 0) {
            EV << "[ERROR] Invalid 'mean' or 'std_dev' for lognormal distribution.\n";
            endSimulation();
            return;
        }

        x = lognormal(mean, std_dev, 0);
        y = lognormal(mean, std_dev, 1);

        EV << "[DEBUG] User " << getIndex() << " positioned lognormally at (" << x << ", " << y << ")\n";
    }

    // Aggiorna la posizione nel display string
    getDisplayString().setTagArg("p", 0, x);
    getDisplayString().setTagArg("p", 1, y);

    cMessage *sendEvent = new cMessage("sendEvent");
    double taskInterval = exponential(intervalRate, 2);  
    scheduleAt(simTime() + taskInterval, sendEvent);  
}

void User::handleMessage(cMessage *msg) {
    if (strcmp(msg->getName(), "sendEvent") == 0) {
        // Messaggio di invio di un task
        cPacket *task = new cPacket("Task");

        double taskSize = exponential(1/sizeRate, 2);
        if (taskSize <= 0) {
            EV << "[WARNING] Generated taskSize <= 0 (" << taskSize << "). Setting to default (1 byte).\n";
            taskSize = 1.0;
        }
        task->setByteLength(static_cast<int>(taskSize));  

        // Trova la BaseStation più vicina
        cModule *nearestBaseStation = findNearestBaseStation();
        if (!nearestBaseStation) {
            EV << "[ERROR] No nearest BaseStation found. Dropping task: " << task->getName() << "\n";
            delete task;
        }
        else {
            EV << "[DEBUG] Sending task: " << task->getName() << " to BaseStation: " << nearestBaseStation->getFullName() << "\n";
            sendDirect(task, nearestBaseStation, "in");
        }

        // Pianifica il prossimo sendEvent
        double taskInterval = exponential(1/intervalRate, 3);
        if (taskInterval <= 0) {
            EV << "[WARNING] Generated taskInterval <= 0 (" << taskInterval << "). Setting to default (1 second).\n";
            taskInterval = 1.0;
        }

        cMessage *sendEventNew = new cMessage("sendEvent");
        scheduleAt(simTime() + taskInterval, sendEventNew);  
        
        delete msg;
    }
    else {
        // Messaggio sconosciuto
        EV << "[ERROR] Received unknown message: " << msg->getName() << "\n";
        delete msg;  
    }
}

cModule* User::findNearestBaseStation() {
    // Trova la BaseStation più vicina all'utente
    cModule *parent = getParentModule();
    if (!parent) {
        EV << "[ERROR] Parent module not found while searching for the nearest BaseStation.\n";
        return nullptr;
    }

    int numBaseStations = parent->par("numBaseStations").intValue();  
    if (numBaseStations <= 0) {
        EV << "[ERROR] Invalid number of BaseStations: " << numBaseStations << "\n";
        return nullptr;
    }

    cModule *nearest = nullptr;
    double minDistance = INFINITY;  

    for (int i = 0; i < numBaseStations; ++i) {
        cModule *baseStation = parent->getSubmodule("baseStations", i); 

        if (!baseStation) {
            EV << "[WARNING] BaseStation module 'baseStations[" << i << "]' not found.\n";
            continue;
        }

        BaseStation *bs = dynamic_cast<BaseStation*>(baseStation);
        if (!bs) {
            EV << "[ERROR] Failed to cast BaseStation module " << i << " to BaseStation.\n";
            continue;
        }

        double baseX = bs->get_x();
        double baseY = bs->get_y();

        // Controlla se le coordinate sono valide
        if (baseX < 0 || baseY < 0) {
            EV << "[WARNING] BaseStation " << i << " has invalid coordinates (" << baseX << ", " << baseY << "). Skipping.\n";
            continue;
        }

        double distance = std::sqrt(std::pow(baseX - x, 2) + std::pow(baseY - y, 2));

        if (distance < minDistance) {
            minDistance = distance;
            nearest = baseStation; 
        }
    }

    return nearest;  
}

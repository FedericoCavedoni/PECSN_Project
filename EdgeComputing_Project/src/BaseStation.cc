#include "BaseStation.h"
#include <cmath>
#include <climits> 

Define_Module(BaseStation);

BaseStation::~BaseStation() {
    // Dealloca tutti i pacchetti rimasti nella coda
    while (taskQueue.size() > 0) {
        cPacket *pkt = taskQueue.front();
        taskQueue.pop();
        delete pkt;
    }
}

void BaseStation::initialize() {
    serviceRate = par("serviceRate").doubleValue();
    delay = par("delay").doubleValue();
    queueSize = par("queueSize").intValue();

    cModule *parent = getParentModule();
    if (!parent) {
        EV << "[ERROR] Parent module not found.\n";
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

    if (!parent->hasPar("numBaseStations")) {
        EV << "[ERROR] Parent module missing 'numBaseStations' parameter.\n";
        endSimulation();
        return;
    }

    numBaseStations = parent->par("numBaseStations").intValue();

    if (numBaseStations <= 0) {
        EV << "[ERROR] Invalid number of base stations: " << numBaseStations << "\n";
        endSimulation();
        return;
    }

    int gridRows = static_cast<int>(floor(sqrt(static_cast<double>(numBaseStations))));
    int gridCols = static_cast<int>(ceil(static_cast<double>(numBaseStations) / static_cast<double>(gridRows)));

    int myIndex = getIndex();
    int row = myIndex / gridCols;
    int col = myIndex % gridCols;

    double cellWidth = static_cast<double>(width) / static_cast<double>(gridCols);
    double cellHeight = static_cast<double>(height) / static_cast<double>(gridRows);

    x = (col + 0.5) * cellWidth;
    y = (row + 0.5) * cellHeight;

    // Aggiorna la posizione nel display string
    getDisplayString().setTagArg("p", 0, x);
    getDisplayString().setTagArg("p", 1, y);

    EV << "[DEBUG] BaseStation " << myIndex << " positioned at (" << x << ", " << y << ")\n";
}

void BaseStation::handleMessage(cMessage *msg) {
    EV << "[DEBUG] Received message: " << msg->getName() << " of type: " << msg->getClassName() << " at time: " << simTime() << "\n";

    if (msg->isSelfMessage()) {
        if (strcmp(msg->getName(), "processNextTask") == 0) {

            // Processa il prossimo task nella coda
            if (taskQueue.size() > 0) {
                cPacket *nextPkt = taskQueue.front();
                taskQueue.pop();
                EV << "[DEBUG] Task dequeued. Queue size: " << taskQueue.size() << "\n";

                if (!nextPkt) {
                    EV << "[ERROR] nextPkt is nullptr. Skipping processing.\n";
                    delete msg; 
                    return;
                }

                double length = nextPkt->getByteLength();
                if (length <= 0) {
                    EV << "[WARNING] Invalid packet length: " << length << ". Setting to default (1 byte).\n";
                    length = 1.0;
                }

                if (serviceRate <= 0) {
                    EV << "[ERROR] Invalid serviceRate: " << serviceRate << ". Cannot compute processingTime. Setting to default (1 unit).\n";
                    processingTime = 1.0;
                }
                else {
                    processingTime = length / serviceRate;
                }

                scheduleAt(simTime() + processingTime, nextPkt); 
            }
            else {
                EV << "[DEBUG] Queue is empty. No tasks to process.\n";
            }

            delete msg;
        }
        else {
            EV << "[WARNING] Received unexpected self-message: " << msg->getName() << "\n";
            delete msg;
        }
    }
    else {
        // Messaggio in arrivo da fuori la baseStation
        if (strcmp(msg->getName(), "Task") != 0) {
            EV << "[ERROR] Unexpected message name: " << msg->getName() << ". Discarding.\n";
            delete msg;
            return;
        }

        cPacket *pkt = nullptr;
        try {
            pkt = check_and_cast<cPacket *>(msg);
        }
        catch (std::bad_cast& e) {
            EV << "[ERROR] Failed to cast incoming message to cPacket: " << e.what() << ". Discarding message.\n";
            delete msg;
            return;
        }

        if (!pkt) {
            EV << "[ERROR] Incoming packet is nullptr after casting. Discarding message.\n";
            delete msg;
            return;
        }

        if (static_cast<int>(taskQueue.size()) < queueSize) {
            if (taskQueue.size() == 0) {
                // Coda vuota: programma il task immediatamente
                EV << "[DEBUG] Queue is empty, scheduling task immediately.\n";
                taskQueue.push(pkt);

                double length = pkt->getByteLength();
                if (length <= 0) {
                    EV << "[WARNING] Invalid packet length: " << length << ". Setting to default (1 byte).\n";
                    length = 1.0;
                }

                if (serviceRate <= 0) {
                    EV << "[ERROR] Invalid serviceRate: " << serviceRate << ". Cannot compute processingTime. Setting to default (1 unit).\n";
                    processingTime = 1.0;
                }
                else {
                    processingTime = length / serviceRate;
                }

                cMessage *processMsg = new cMessage("processNextTask");
                scheduleAt(simTime() + processingTime, processMsg);
            }
            else {
                // Coda non vuota: aggiungi il task in coda
                taskQueue.push(pkt);
                EV << "[DEBUG] Task enqueued. New queue size: " << taskQueue.size() << "\n";
            }
        }
        else {
            // Coda piena: cerca una BaseStation meno carica
            EV << "[DEBUG] Queue full. Searching for the best BaseStation to forward the task.\n";
            cModule *bestBS = findBestBaseStation();
            if (bestBS == nullptr) {
                EV << "[ERROR] No free queue found. Dropping task: " << pkt->getName() << "\n";
                delete pkt;
            }
            else {
                EV << "[DEBUG] Forwarding task: " << pkt->getName() << " to BaseStation: " << bestBS->getFullName() << "\n";
                sendDirect(pkt, bestBS, "in");
            }
        }
    }
}

cModule* BaseStation::findBestBaseStation() {
    // Cerca la BaseStation con la coda più corta
    cModule *parent = getParentModule();
    if (!parent) {
        EV << "[ERROR] Parent module not found while searching for the best BaseStation.\n";
        return nullptr;
    }

    cModule* bestBS = nullptr;
    int bestQueue = INT_MAX;

    for (int i = 0; i < numBaseStations; i++) {
        if (i == getIndex()) 
            continue; 

        cModule *mod = parent->getSubmodule("baseStations", i); 

        if (!mod) {
            EV << "[WARNING] BaseStation module 'baseStations[" << i << "]' not found.\n";
            continue;
        }

        BaseStation *bs = dynamic_cast<BaseStation*>(mod);
        if (!bs) {
            EV << "[ERROR] Failed to cast BaseStation module " << i << " to BaseStation.\n";
            continue;
        }

        int qlen = bs->getQueueLength();

        if (qlen == 0) {
            return mod;
        }

        if (qlen < bs->queueSize && qlen < bestQueue) {
            bestQueue = qlen;
            bestBS = mod;
        }
    }

    return bestBS;
}

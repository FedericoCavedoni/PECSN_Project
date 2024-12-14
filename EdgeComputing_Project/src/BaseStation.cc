// BaseStation.cc
#include "BaseStation.h"
#include <cmath>
#include <climits>

Define_Module(BaseStation);

BaseStation::~BaseStation() {
    // Dealloca tutti i pacchetti rimasti nella coda
    while (taskQueue.size() > 0) {
        QueuePacket *pkt = taskQueue.front();
        taskQueue.pop();
        delete pkt;
    }
}

void BaseStation::initialize() {
    serviceRate = par("serviceRate").doubleValue();
    delay = par("delay").doubleValue();
    queueSize = par("queueSize").intValue();

    responseTimeSignal_ = registerSignal("responseTimeSignal");
    queueLengthSignal_ = registerSignal("queueLengthSignal");
    forwardedSignal_ = registerSignal("forwardedSignal");
    droppedSignal_ = registerSignal("droppedSignal");

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

    emit(queueLengthSignal_, (double)taskQueue.size());
}

void BaseStation::handleMessage(cMessage *msg) {
    if (msg->isSelfMessage()) {
        if (strcmp(msg->getName(), "processNextTask") == 0) {
            // Processa il prossimo task nella coda
            if (taskQueue.size() > 0) {
                QueuePacket *nextPkt = taskQueue.front();
                taskQueue.pop();
                emit(queueLengthSignal_, (double)taskQueue.size());
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

                simtime_t processingTime;
                if (serviceRate <= 0) {
                    EV << "[ERROR] Invalid serviceRate: " << serviceRate << ". Cannot compute processingTime. Setting to default (1 unit).\n";
                    processingTime = 1.0;
                }
                else {
                    processingTime = length / serviceRate;
                }

                // Calcolo del response time usando arrivalTime
                simtime_t responseTime = simTime() - nextPkt->getArrivalTime() + processingTime;
                emit(responseTimeSignal_, responseTime);

                // Elimina il pacchetto dopo l'elaborazione
                delete nextPkt;

                // Programma il prossimo task se la coda non è vuota
                if (taskQueue.size() > 0) { 
                    cMessage *processMsg = new cMessage("processNextTask");
                    scheduleAt(simTime() + processingTime, processMsg); 
                }

                delete msg; // Elimina il selfMessage
            }
            else {
                EV << "[DEBUG] Queue is empty. No tasks to process.\n";
                delete msg;
            }
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

        // Cast a cPacket
        cPacket *incomingPkt = dynamic_cast<cPacket *>(msg);
        if (!incomingPkt) {
            EV << "[ERROR] Incoming message is not a cPacket. Discarding.\n";
            delete msg;
            return;
        }

        EV << "[DEBUG] Received task. ";
        EV << "Packet name: " << incomingPkt->getName();
        EV << ", Packet length: " << incomingPkt->getByteLength() << "\n";

        // Converti cPacket in QueuePacket
        QueuePacket *queuePkt = new QueuePacket(incomingPkt->getName());
        queuePkt->setByteLength(incomingPkt->getByteLength());
        queuePkt->setArrivalTime(simTime().dbl());

        // Elimina il cPacket originale se non necessario
        delete incomingPkt;

        if (taskQueue.size() < queueSize) {
            if (taskQueue.size() == 0) {
                // Coda vuota: programma il task immediatamente
                EV << "[DEBUG] Queue is empty, scheduling task immediately.\n";
                taskQueue.push(queuePkt);
                emit(queueLengthSignal_, (double)taskQueue.size());

                double length = queuePkt->getByteLength();
                if (length <= 0) {
                    EV << "[WARNING] Invalid packet length: " << length << ". Setting to default (1 byte).\n";
                    length = 1.0;
                }

                simtime_t processingTime;
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
                taskQueue.push(queuePkt);
                emit(queueLengthSignal_, (double)taskQueue.size());
                EV << "[DEBUG] Task enqueued. New queue size: " << taskQueue.size() << "\n";
            }
        }
        else {
            // Coda piena: cerca una BaseStation meno carica
            EV << "[DEBUG] Queue full. Searching for the best BaseStation to forward the task.\n";
            cModule *bestBS = findBestBaseStation();
            if (bestBS == nullptr) {
                EV << "[ERROR] No free queue found. Dropping task: " << queuePkt->getName() << "\n";
                emit(droppedSignal_, 1);
                delete queuePkt;
            }
            else {
                EV << "[DEBUG] Forwarding task: " << queuePkt->getName() << " to BaseStation: " << bestBS->getFullName() << "\n";
                emit(forwardedSignal_, 1);
                sendDirect(queuePkt, delay, 0, bestBS, "in");
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

#include "BaseStation.h"
#include <cmath>
#include <climits> // per INT_MAX

Define_Module(BaseStation);

void BaseStation::initialize() {
    serviceRate = par("serviceRate");
    delay = par("delay");
    queueSize = par("queueSize");

    cModule *parent = getParentModule();
    int width = parent->par("width");
    int height = parent->par("height");

    numBaseStations = parent->par("numBaseStations");

    int gridRows = (int)floor(sqrt((double)numBaseStations));
    int gridCols = (int)ceil((double)numBaseStations / (double)gridRows);

    int myIndex = getIndex();
    int row = myIndex / gridCols;
    int col = myIndex % gridCols;

    double cellWidth = (double)width / (double)gridCols;
    double cellHeight = (double)height / (double)gridRows;

    x = (col + 0.5) * cellWidth;
    y = (row + 0.5) * cellHeight;

    // Aggiorna la posizione nel display string
    getDisplayString().setTagArg("p", 0, x);
    getDisplayString().setTagArg("p", 1, y);

    EV << "[DEBUG] BaseStation " << myIndex << " positioned at (" << x << ", " << y << ")\n";
}

void BaseStation::handleMessage(cMessage *msg) {

    EV << "[DEBUG] Received message: " << msg->getName() 
       << " of type: " << msg->getClassName() << " at time: " << simTime() << "\n";

    // Controllo il nome del pacchetto
    if (strcmp(msg->getName(), "Task") != 0) {
        EV << "[ERROR] Unexpected message name: " << msg->getName() << ". Discarding.\n";
        delete msg;
        return;
    }

    // Messaggio preso dalla coda
    if (msg->isSelfMessage()) {
        EV << "[DEBUG] Handling self-message.\n";

        // Aggiungi stampa prima del cast
        EV << "[DEBUG] Attempting to cast self-message to cPacket.\n";

        // Cast a cPacket
        cPacket *pkt = nullptr;
        try {
            pkt = check_and_cast<cPacket *>(msg);
            EV << "[DEBUG] Successfully casted self-message to cPacket.\n";
        }
        catch (std::bad_cast& e) {
            EV << "[ERROR] Failed to cast self-message to cPacket: " << e.what() << ". Discarding message.\n";
            delete msg;
            return;
        }

        EV << "[DEBUG] Processing task: " << pkt->getName() 
           << " with size: " << pkt->getByteLength() << " bytes.\n";

        // Elaborazione completata
        delete pkt; 
        pkt = nullptr;

        // Se c'è un altro task in coda, processa il prossimo
        if (!taskQueue.empty()) {
            cPacket *nextPkt = taskQueue.front();
            taskQueue.pop();
            EV << "[DEBUG] Task dequeued. Queue size: " << taskQueue.size() << "\n";

            // Aggiungi stampa prima di schedulare
            EV << "[DEBUG] Scheduling next task: " << nextPkt->getName() 
               << " with size: " << nextPkt->getByteLength() << " bytes.\n";

            double processingTime = nextPkt->getByteLength() / serviceRate;
            scheduleAt(simTime() + processingTime, nextPkt);
            EV << "[DEBUG] Next task scheduled at time: " << simTime() + processingTime << "\n";
        } else {
            EV << "[DEBUG] Queue is empty. No tasks to process.\n";
        }
    } else {
        // Messaggio dall'esterno
        EV << "[DEBUG] Received task from outside. Current queue size: " << taskQueue.size() << "\n";

        // Aggiungi stampa prima del cast
        EV << "[DEBUG] Attempting to cast incoming message to cPacket.\n";

        // Cast a cPacket
        cPacket *pkt = nullptr;
        try {
            pkt = check_and_cast<cPacket *>(msg);
            EV << "[DEBUG] Successfully casted incoming message to cPacket.\n";
        }
        catch (std::bad_cast& e) {
            EV << "[ERROR] Failed to cast incoming message to cPacket: " << e.what() << ". Discarding message.\n";
            delete msg;
            return;
        }

        if ((int)taskQueue.size() < queueSize) {
            // Coda non piena
            if (taskQueue.empty()) {
                EV << "[DEBUG] Queue is empty: enqueue task and schedule immediately.\n";
                taskQueue.push(pkt); // Mettiamo in coda
                cPacket *immediateTask = taskQueue.front();
                taskQueue.pop(); // Rimuoviamo subito dalla coda per schedularlo
                EV << "[DEBUG] Scheduling immediate task: " << immediateTask->getName() 
                   << " with size: " << immediateTask->getByteLength() << " bytes.\n";
                double processingTime = immediateTask->getByteLength() / serviceRate;
                scheduleAt(simTime() + processingTime, immediateTask);
                EV << "[DEBUG] Immediate task scheduled at time: " << simTime() + processingTime << "\n";
            } else {
                // Coda non vuota, aggiungi in coda
                EV << "[DEBUG] Queue not empty: enqueue task.\n";
                taskQueue.push(pkt);
                EV << "[DEBUG] Task enqueued. New queue size: " << taskQueue.size() << "\n";
                // Non scheduliamo ora, verrà gestito quando l'attuale task finirà.
            }
        } else {
            // Coda piena: cerchiamo una BaseStation meno carica
            EV << "[DEBUG] Queue full. Searching for the best BaseStation to forward the task.\n";
            cModule *bestBS = findBestBaseStation();
            if (bestBS == nullptr) {
                EV << "[ERROR] No free queue found. Dropping task: " << pkt->getName() << "\n";
                delete pkt;
            } else {
                EV << "[DEBUG] Forwarding task: " << pkt->getName() 
                   << " to BaseStation: " << bestBS->getFullName() << "\n";
                sendDirect(pkt, bestBS, "in");
            }
        }
    }
}

cModule* BaseStation::findBestBaseStation() {
    // Cercare il BS con la coda più corta
    cModule *parent = getParentModule();
    EV << "[DEBUG] Searching for the best BaseStation among " << numBaseStations << " stations.\n";

    cModule* bestBS = nullptr;
    int bestQueue = INT_MAX; 

    for (int i = 0; i < numBaseStations; i++) {
        if (i == getIndex()) 
            continue; // Salta la stazione attuale
        
        cModule *mod = parent->getSubmodule("baseStation", i);
        if (!mod) {
            EV << "[WARNING] BaseStation module " << i << " not found.\n";
            continue;
        }

        BaseStation *bs = dynamic_cast<BaseStation*>(mod);
        if (!bs) {
            EV << "[ERROR] Failed to cast BaseStation module " << i << " to BaseStation.\n";
            continue;
        }

        int qlen = bs->getQueueLength();
        EV << "[DEBUG] Evaluating BaseStation " << i 
           << ": queue length = " << qlen 
           << ", capacity = " << bs->queueSize << "\n";

        if (qlen == 0) {
            EV << "[DEBUG] Found an empty BaseStation: " << mod->getFullName() << "\n";
            return mod;
        }

        if (qlen < bs->queueSize && qlen < bestQueue) {
            EV << "[DEBUG] Found a better BaseStation with smaller queue: " 
               << mod->getFullName() << "\n";
            bestQueue = qlen;
            bestBS = mod;
        }
    }

    if (bestBS == nullptr) {
        EV << "[ERROR] No suitable BaseStation found.\n";
    } else {
        EV << "[DEBUG] Best BaseStation selected: " << bestBS->getFullName() << "\n";
    }
    return bestBS;
}

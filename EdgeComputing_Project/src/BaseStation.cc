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

    int gridSize = (int)ceil(sqrt((double)numBaseStations));

    int myIndex = getIndex();
    int row = myIndex / gridSize;
    int col = myIndex % gridSize;

    // Posizionamento della Base Station
    x = (col + 0.5) * (width / gridSize);
    y = (row + 0.5) * (height / gridSize);

    // Aggiorna la posizione nel display string
    getDisplayString().setTagArg("p", 0, x);
    getDisplayString().setTagArg("p", 1, y);

    EV << "BaseStation " << myIndex << " positioned at (" << x << ", " << y << ")\n";
}

void BaseStation::handleMessage(cMessage *msg) {
    if (msg->isSelfMessage()) {
        // Messaggio interno di scheduling
        cPacket *pkt = check_and_cast<cPacket *>(msg);
        EV << "Processing self-message: " << pkt->getName() << "\n";
        delete pkt;

        if (!taskQueue.empty()) {
            cMessage *nextTask = taskQueue.front();
            taskQueue.pop();
            scheduleAt(simTime() + 1 / serviceRate, nextTask);
        }
    } else {
        // Messaggio in arrivo dall'esterno (utente o altra basestation)
        if ((int)taskQueue.size() < queueSize) {
            // C'è spazio in coda, accodiamo
            taskQueue.push(msg);
            if (taskQueue.size() == 1) {
                scheduleAt(simTime() + 1 / serviceRate, msg);
            }
        } else {
            // Coda piena, cerchiamo una BaseStation meno carica o vuota
            cModule *bestBS = findBestBaseStation();
            if (bestBS == nullptr) {
                // Nessuna stazione disponibile, scartiamo il messaggio
                EV << "No free queue found. Dropping message: " << msg->getName() << "\n";
                delete msg;
            } else {
                EV << "Forwarding message: " << msg->getName() << " to " << bestBS->getFullName() << "\n";
                sendDirect(msg, bestBS, "in");
            }
        }
    }
}

cModule* BaseStation::findBestBaseStation() {
    cModule *parent = getParentModule();

    cModule* bestBS = nullptr;
    int bestQueue = INT_MAX; 

    for (int i = 0; i < numBaseStations; i++) {
        if (i == getIndex()) continue; // Salta la stazione attuale
        cModule *mod = parent->getSubmodule("baseStation", i);
        BaseStation *bs = check_and_cast<BaseStation *>(mod);
        int qlen = bs->getQueueLength();

        // Prima priorità: se troviamo una base station con coda vuota, restituiamola subito
        if (qlen == 0) {
            return mod;
        }

        // Altrimenti teniamo traccia di quella con la coda meno piena
        if (qlen < bs->queueSize && qlen < bestQueue) {
            bestQueue = qlen;
            bestBS = mod;
        }
    }

    return bestBS; // se non ne troviamo nessuna vuota, restituiamo la meno piena, o nullptr se non c'è
}

#include "BaseStation.h"

Define_Module(BaseStation);

void BaseStation::initialize() {
    serviceRate = par("serviceRate");
    delay = par("delay");

    cModule *parent = getParentModule();
    double width = parent->par("width");
    double height = parent->par("height");
    int numBaseStations = parent->par("numBaseStations");
    int gridSize = ceil(sqrt(numBaseStations)); // Calcola la dimensione della griglia (es: 4x4 per 10 nodi)

    int myIndex = getIndex();
    int row = myIndex / gridSize;
    int col = myIndex % gridSize;

    x = (col + 0.5) * (width / gridSize);
    y = (row + 0.5) * (height / gridSize);


    EV << "BaseStation " << myIndex << " positioned at (" << x << ", " << y << ")\n";


    for (int i = 0; i < numBaseStations; ++i) {
        if (i != myIndex) {
            cModule *otherBaseStation = parent->getSubmodule("baseStations", i);

            cGate *outGate = gate("out", i);
            cGate *inGate = otherBaseStation->gate("in", myIndex);

            cDelayChannel *delayChannel = cDelayChannel::create("meshDelayChannel");
            delayChannel->setDelay(delay / 1000.0);

            outGate->connectTo(inGate, delayChannel);
        }
    }
}



void BaseStation::handleMessage(cMessage *msg) {
    if (msg->isSelfMessage()) {
        delete msg;
        if (!taskQueue.empty()) {
            cMessage *nextTask = taskQueue.front();
            taskQueue.pop();
            scheduleAt(simTime() + 1 / serviceRate, nextTask);
        }
    } else {
        if (taskQueue.size() > 10) {
            cModule *parent = getParentModule();
            int numBaseStations = parent->par("numBaseStations");

            cModule *leastLoadedBS = nullptr;
            int minQueueSize = INT_MAX;

            for (int i = 0; i < numBaseStations; ++i) {
                cModule *otherBaseStation = parent->getSubmodule("baseStations", i);
                if (otherBaseStation != this) {
                    BaseStation *bs = check_and_cast<BaseStation *>(otherBaseStation);
                    if ((int)bs->taskQueue.size() < minQueueSize) {
                        minQueueSize = bs->taskQueue.size();
                        leastLoadedBS = bs;
                    }
                }
            }

            if (leastLoadedBS) {
                int index = leastLoadedBS->getIndex();
                send(msg, "out", index);
            }
        } else {
            taskQueue.push(msg);
            if (taskQueue.size() == 1) {
                scheduleAt(simTime() + 1 / serviceRate, msg);
            }
        }
    }
}

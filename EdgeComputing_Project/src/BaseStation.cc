#include "BaseStation.h"
#include <cmath>
#include <climits>

Define_Module(BaseStation);

BaseStation::~BaseStation() {
    while (!taskQueue.empty()) {
        QueuePacket *pkt = taskQueue.front();
        taskQueue.pop();
        delete pkt;
    }
    delete activeTask;
    activeTask = nullptr;
}

void BaseStation::initialize() {
    serviceRate = par("serviceRate").doubleValue();
    delay = par("delay").doubleValue();
    queueSize = par("queueSize").intValue();
    locallyManaged = par("locallyManaged").boolValue();
    activeTask = nullptr;

    responseTimeSignal_ = registerSignal("responseTimeSignal");
    queueLengthSignal_ = registerSignal("queueLengthSignal");
    forwardedSignal_ = registerSignal("forwardedSignal");
    droppedSignal_ = registerSignal("droppedSignal");

    idle = true;

    cModule *parent = getParentModule();
    if (!parent) {
        EV << "[ERROR] Parent module not found.\n";
        endSimulation();
        return;
    }

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

    int width = parent->par("width").intValue();  
    int height = parent->par("height").intValue(); 

    int gridRows = (int)floor(sqrt((double)numBaseStations));
    int gridCols = (int)ceil((double)numBaseStations / (double)gridRows);

    int myIndex = getIndex();
    int row = myIndex / gridCols;
    int col = myIndex % gridCols;

    double cellWidth = (double)width / (double)gridCols;
    double cellHeight = (double)height / (double)gridRows;

    x = (col + 0.5) * cellWidth;
    y = (row + 0.5) * cellHeight;

    getDisplayString().setTagArg("p", 0, x);
    getDisplayString().setTagArg("p", 1, y);

    EV << "[DEBUG] BaseStation " << myIndex << " positioned at (" << x << ", " << y << ")\n";

    emit(queueLengthSignal_, (double)taskQueue.size());
}

void BaseStation::handleMessage(cMessage *msg) {
    if (msg->isSelfMessage()) {
        if (strcmp(msg->getName(), "processNextTask") == 0) {
            handleProcessNextTaskMessage();
            delete msg;
        } else {
            EV << "[WARNING] Received unexpected self-message: " << msg->getName() << "\n";
            delete msg;
        }
    } else {
        if (strcmp(msg->getName(), "Task") == 0) {
            cPacket *incomingPkt = dynamic_cast<cPacket *>(msg);
            if (!incomingPkt) {
                EV << "[ERROR] Incoming message is not a cPacket. Discarding.\n";
                delete msg;
            } else {
                handleNewTask(incomingPkt);
            }
        } 
        else if (strcmp(msg->getName(), "ForwardedPacket") == 0) {
            QueuePacket *queuePkt = dynamic_cast<QueuePacket *>(msg);
            if (!queuePkt) {
                EV << "[ERROR] Incoming message is not a QueuePacket. Discarding.\n";
                delete msg;
            } else {
                handleForwardedPacket(queuePkt);
            }
        } 
        else {
            EV << "[WARNING] Received unexpected message: " << msg->getName() << "\n";
            delete msg;
        }
    }
}

void BaseStation::handleProcessNextTaskMessage() {
    if (!taskQueue.empty()) {
        idle = false; 
        processNextTask();
    } else {
        delete activeTask;
        activeTask = nullptr;
        idle = true;
        EV << "[DEBUG] Queue is empty. No tasks to process.\n";
    }
}

void BaseStation::processNextTask() {
    if(activeTask){
        delete activeTask;
        activeTask = nullptr;
    }
    activeTask = taskQueue.front();
    taskQueue.pop();
    emit(queueLengthSignal_, (double)taskQueue.size());
    EV << "[DEBUG] Task dequeued. Queue size: " << taskQueue.size() << "\n";

    if (!activeTask) {
        EV << "[ERROR] activeTask is nullptr. Skipping processing.\n";
        return;
    }

    double length = activeTask->getByteLength();
    if (length <= 0) {
        EV << "[WARNING] Invalid packet length: " << length << ". Setting to default (1 byte).\n";
        length = 1.0;
    }

    simtime_t processingTime = (serviceRate > 0) ? length / serviceRate : 1.0;
    simtime_t responseTime = simTime() - activeTask->getCreationTime();
    emit(responseTimeSignal_, responseTime + processingTime);

    scheduleNextTaskProcessing(processingTime);    
}

void BaseStation::scheduleNextTaskProcessing(simtime_t processingTime) {
    cMessage *processMsg = new cMessage("processNextTask");
    scheduleAt(simTime() + processingTime, processMsg);
}

void BaseStation::enqueueTask(QueuePacket* pkt) {
    bool wasEmpty = (taskQueue.size() == 0);

    if (wasEmpty && idle) {
        activeTask = pkt;
        idle = false;  
        double length = pkt->getByteLength();
        if (length <= 0) {
            EV << "[WARNING] Invalid packet length: " << length << ". Setting to 1 byte.\n";
            length = 1.0;
        }
        simtime_t processingTime = (serviceRate > 0) ? length / serviceRate : 1.0;
        simtime_t responseTime = simTime() - activeTask->getCreationTime();
        emit(responseTimeSignal_, responseTime + processingTime);

        scheduleNextTaskProcessing(processingTime);
    } else {
        taskQueue.push(pkt);
        emit(queueLengthSignal_, (double)taskQueue.size());
        EV << "[DEBUG] Task enqueued. Queue size: " << taskQueue.size() << "\n";
    }
}

void BaseStation::handleNewTask(cPacket* incomingPkt) {
    EV << "[DEBUG] Received task. Packet name: " << incomingPkt->getName()
       << ", Packet length: " << incomingPkt->getByteLength() << "\n";

    QueuePacket *queuePkt = new QueuePacket("ForwardedPacket");
    queuePkt->setByteLength(incomingPkt->getByteLength());
    queuePkt->setCreationTime(simTime().dbl());
    delete incomingPkt;

    if (locallyManaged) {
        if ((int)taskQueue.size() < queueSize) {
            enqueueTask(queuePkt);
        } else {
            EV << "[DEBUG] Queue is full. Dropping task.\n";
            emit(droppedSignal_, 1.0);
            delete queuePkt;
        }
    } else {
        cModule *bestBS = findBestBaseStation();
        int ourQueueLength = (int)taskQueue.size();
        int bestQueueLength = INT_MAX;

        if (bestBS) {
            BaseStation *bs = dynamic_cast<BaseStation*>(bestBS);
            if (bs) {
                bestQueueLength = bs->getQueueLength();
            }
        }

        if (bestBS != nullptr && ourQueueLength > bestQueueLength) {
            EV << "[DEBUG] Forwarding task: " << queuePkt->getName() 
               << " to BaseStation: " << bestBS->getFullName()
               << " (ourQ=" << ourQueueLength << ", bestQ=" << bestQueueLength << ")\n";
            emit(forwardedSignal_, 1);
            sendDirect(queuePkt, delay, 0, bestBS, "in");
        } else {
            if (ourQueueLength < queueSize) {
                EV << "[DEBUG] Managing task locally as our queue is not worse than best found.\n";
                enqueueTask(queuePkt);
            } else {
                EV << "[DEBUG] Queue is full. Dropping task.\n";
                emit(droppedSignal_, 1.0);
                delete queuePkt;
            }
        }
    }
}

void BaseStation::handleForwardedPacket(QueuePacket* queuePkt) {
    EV << "[DEBUG] Handling forwarded packet.\n";
    if ((int)taskQueue.size() < queueSize) {
        enqueueTask(queuePkt);
    } else {
        EV << "[DEBUG] Queue is full. Dropping forwarded task.\n";
        emit(droppedSignal_, 1.0);
        delete queuePkt;
    }
}

cModule* BaseStation::findBestBaseStation() {
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

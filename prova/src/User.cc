#include "User.h"
#include "BaseStation.h"

Define_Module(User);

void User::initialize() {
    intervalRate = par("intervalRate");
    sizeRate = par("sizeRate");

    if (par("uniformDistribution").boolValue()) {
        cModule *parent = getParentModule();
        double width = parent->par("width");
        double height = parent->par("height");

        x = uniform(0, width, 0);
        y = uniform(0, height, 1);
    } else {
        double mean = par("mean");
        double std_dev = par("std_dev");

        x = lognormal(mean, std_dev, 0);
        y = lognormal(mean, std_dev, 1);
    }

    cModule *nearestBaseStation = findNearestBaseStation();
    if (nearestBaseStation) {
        cGate *userOut = gate("out");
        cGate *baseIn = nearestBaseStation->gate("in");
        userOut->connectTo(baseIn);
    }

    sendEvent = new cMessage("sendEvent");

    taskInterval = exponential(intervalRate);

    scheduleAt(simTime() + taskInterval, sendEvent);
}

void User::handleMessage(cMessage *msg) {
    if (msg == sendEvent) {
        generateAndSendTask();

        taskInterval = exponential(intervalRate);

        scheduleAt(simTime() + taskInterval, sendEvent);
    } else {
        delete msg;
    }
}

void User::generateAndSendTask() {
    cPacket *task = new cPacket("Task");

    taskSize = exponential(sizeRate);
    task->setByteLength(taskSize);

    send(task, "out");
}

cModule *User::findNearestBaseStation() {
    cModule *parent = getParentModule();
    int numBaseStations = parent->par("numBaseStations");
    cModule *nearest = nullptr;
    double minDistance = INFINITY;

    for (int i = 0; i < numBaseStations; ++i) {
        cModule *baseStation = parent->getSubmodule("baseStations", i);

        BaseStation *bs = check_and_cast<BaseStation *>(baseStation);
        double baseX = bs->x;
        double baseY = bs->y;

        double distance = std::sqrt(std::pow(baseX - x, 2) + std::pow(baseY - y, 2));
        if (distance < minDistance) {
            minDistance = distance;
            nearest = baseStation;
        }
    }

    return nearest;
}


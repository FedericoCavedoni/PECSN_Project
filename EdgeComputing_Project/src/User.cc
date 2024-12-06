#include "User.h"
#include "BaseStation.h"

Define_Module(User);

void User::initialize(int stage) {
    intervalRate = par("intervalRate");
    sizeRate = par("sizeRate");

    nearestBaseStation = findNearestBaseStation();

    if (par("uniformDistribution").boolValue()) {
        cModule *parent = getParentModule();
        int width = parent->par("width");
        int height = parent->par("height");

        x = uniform(0, width, 0);
        y = uniform(0, height, 1);

    } else {
        int mean = par("mean");
        int std_dev = par("std_dev");

        x = lognormal(mean, std_dev, 0);
        y = lognormal(mean, std_dev, 1);

    }

    getDisplayString().setTagArg("p", 0, x);
    getDisplayString().setTagArg("p", 1, y);

    sendEvent = new cMessage("sendEvent");
    taskInterval = exponential(intervalRate);

    scheduleAt(simTime() + taskInterval, sendEvent);
}

void User::handleMessage(cMessage *msg) {
    if (msg == sendEvent) {
        cPacket *task = new cPacket("Task");
        taskSize = exponential(sizeRate);
        task->setByteLength(taskSize);

        sendDirect(msg, nearestBaseStation, "in");

        taskInterval = exponential(intervalRate);
        scheduleAt(simTime() + taskInterval, sendEvent);
    } else {
        delete msg;
    }
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

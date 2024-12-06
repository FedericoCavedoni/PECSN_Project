#ifndef __BASESTATION_H_
#define __BASESTATION_H_

#include <omnetpp.h>
#include <queue>

using namespace omnetpp;

class BaseStation : public cSimpleModule {
private:
    double serviceRate;
    double delay;

    int queueSize;
    std::queue<cMessage*> taskQueue;

    double x, y;

    int numBaseStations;

public:
    int getQueueLength() const { return (int)taskQueue.size(); }

protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    cModule* findBestBaseStation();
};

#endif

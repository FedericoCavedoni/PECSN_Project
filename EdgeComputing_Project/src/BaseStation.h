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
    std::queue<cPacket*> taskQueue;

    double x, y;

    int numBaseStations;
    int processingTime;

public:
    int getQueueLength() const { return (int)taskQueue.size(); }
    double get_x() const { return x; }
    double get_y() const { return y; }  

protected:
    ~BaseStation(); 

    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    cModule* findBestBaseStation();
};

#endif

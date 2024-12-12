#ifndef __BASESTATION_H_
#define __BASESTATION_H_

#include <omnetpp.h>
#include <queue>

#include "QueuePacket_m.h"

using namespace omnetpp;

class BaseStation : public cSimpleModule {
private:
    double serviceRate;
    double delay;

    int queueSize;
    std::queue<QueuePacket*> taskQueue;

    double x, y;

    int numBaseStations;

    simsignal_t responseTimeSignal_;
    simsignal_t queueLengthSignal_;
    simsignal_t forwardedSignal_;
    simsignal_t droppedSignal_;

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

#ifndef BASESTATION_H
#define BASESTATION_H

#include <omnetpp.h>
#include <queue>

using namespace omnetpp;

class BaseStation : public cSimpleModule {
  private:

    double delay;
    double serviceRate;

    std::queue<cMessage*> taskQueue;

  public:
    double x;
    double y;

  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
};

#endif // BASESTATION_H

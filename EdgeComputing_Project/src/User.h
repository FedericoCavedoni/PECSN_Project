#ifndef USER_H
#define USER_H

#include <omnetpp.h>

using namespace omnetpp;

class User : public cSimpleModule {
  private:
    double x;
    double y;

    double intervalRate;
    double sizeRate;

  protected:
    ~User() {};

    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    cModule *findNearestBaseStation();
};

#endif // USER_H

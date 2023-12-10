#pragma once
#include "Observer.h"
#include <vector>
#include <memory>
using namespace std;

class Subject: public enable_shared_from_this<Subject>
{
public:
    Subject();
    virtual ~Subject();

    void attach(shared_ptr<Observer> pObserver);
    void detach(shared_ptr<Observer> pObserver);
    void notify();
        
    virtual int getState() = 0;
    virtual void setState(int i)= 0;
    
private:
    vector<shared_ptr<Observer>> m_vtObj;
};

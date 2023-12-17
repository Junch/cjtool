#pragma once
#include "Observer.h"
#include <vector>
#include <memory>

class Subject: public std::enable_shared_from_this<Subject>
{
public:
    Subject();
    virtual ~Subject();

    void attach(std::shared_ptr<Observer> pObserver);
    void detach(std::shared_ptr<Observer> pObserver);
    void notify();
        
    virtual int getState() = 0;
    virtual void setState(int i)= 0;
    
private:
    std::vector<std::shared_ptr<Observer>> m_vtObj;
};

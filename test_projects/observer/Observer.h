#pragma once
#include <memory>

class Subject;

class Observer
{

public:
    Observer();
    virtual ~Observer();
    virtual void update(std::shared_ptr<Subject> sub) = 0;
};

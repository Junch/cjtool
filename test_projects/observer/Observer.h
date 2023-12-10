#pragma once
#include <memory>
using namespace std;

class Subject;

class Observer
{

public:
    Observer();
    virtual ~Observer();
    virtual void update(shared_ptr<Subject> sub) = 0;
};

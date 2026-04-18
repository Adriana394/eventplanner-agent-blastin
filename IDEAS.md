# Ideas for Later

Schema ideas that are not yet implemented but worth revisiting in the future.

## BudgetLevel Enum

A simplified budget tier instead of explicit min/max amounts.
Could be used as an alternative or alongside numeric budgets.

```python
class BudgetLevel(str, Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
```

## MobilityMode Enum

Transport preference for itinerary planning.
Could influence route suggestions and travel time estimates.

```python
class MobilityMode(str, Enum):
    walk = 'walk'
    public_transport = 'public transport'
    car = 'car'
    any = 'no preferences'
```

## Currency Field on Budget

Support for multi-currency budgets (currently hardcoded to EUR).

```python
currency: str = Field(default='EUR', description='Currency code')
```

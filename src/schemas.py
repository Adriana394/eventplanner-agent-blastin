from pydantic import BaseModel, Field, EmailStr, model_validator, conint, confloat
from typing import List, Optional, Literal, Dict
from datetime import date
from enum import Enum


# Structured Inputs

class PlanningMode(str, Enum):
    full_trip = 'full_trip'
    event_day_trip = 'event_day_trip'

# class BudgetLevel(str, Enum):
#     low = 'low'
#     medium = 'medium'
#     high = 'high'
    
     
class TimePreferences(str, Enum):
    daytime = 'daytime'
    evening = 'evening'
    night = 'night'
    any = 'no preferences'
    
    
# class MobilityMode(str, Enum):
#     walk = 'walk'
#     public_transport = 'public transport'
#     car = 'car'
#     any = 'no preferences'


class Language(str, Enum):
    de = 'Deutsch'
    en = 'English'
    
    
class UserProfile(BaseModel):
    name: Optional[str] = Field(default = None, description= 'User name. Only used for personalization')
    

class Budget(BaseModel):
    """ Budget Model.
    User can use budget_level or min/max amounts
    """
    #currency: str = Field(default = 'EUR', description = 'Currency code ')
    #budget_level : Optional[BudgetLevel] = Field(default = None, description = 'Budget tier, e.g. low, medium, high.')
    min_budget : Optional[float] = Field(default = None, description = 'Minimum budget amount.')
    max_budget : Optional[float] = Field(default = None, description = 'Maximum budget amount.')
    
    @model_validator(mode = 'after')
    def validate_min_max(self):
        if self.min_budget is not None and self.max_budget is not None and self.min_budget > self.max_budget:
            raise ValueError('Min budget must be <= max budget')
        return self
   
    
class TripRequest(BaseModel):
    city: str = Field(description= 'City user wants to visit (e.g Munich).')
    country: Optional[str] = Field(default = None, description= ' Optional country name.')
    date_start: date = Field(description= ' Start date of the trip.')
    date_end: date = Field(description= 'End date of the trip.')
    
    planning_mode: PlanningMode = Field(default = PlanningMode.full_trip, description= 'Defines whether the user wants a full trip or only an event/day trip.')
    events_enabled: bool = Field(default = True, description= 'If false, no events should be planned.')
    sightseeing_enabled: bool = Field(default = True, description= 'If false, no sightseeing should be planned.')
    food_drink_enabled: bool = Field(default = True, description= 'If false, no restaurant, bar, or cafe recommendations should be planned.')
    
    group_size: Optional[conint(ge=1, le=15)] = Field(default = None, description= 'Number of travel group.')
    budget: Optional[Budget] = Field(default = None, description= 'Optional budget information.')
    
    @model_validator(mode = 'after')
    def validate_date(self):
        if self.date_end is not None and self.date_end < self.date_start:
            raise ValueError('Date end must be >= date start.')
        return self


class EventPreferences(BaseModel):
    """ Event-related preferences.
    Keep seperate so you can later swap to Eventim API without changing structure
    """
    
    vibe: Optional[str] = Field(default = None, description= 'Desired vibe (e.g., techno, hiphop, rnb)')
    categories: Optional[str] = Field(default = None, description= 'Desired event (e.g., festival, concert, musical)')
    time_pref: TimePreferences = Field(default = TimePreferences.any, description= 'Preferred time for events.')
    free_only: bool = Field(default = False, description= ' If true, only include free events.')
    

class ItineraryPreferences(BaseModel):
    #mobility_mode: MobilityMode = Field(default = MobilityMode.any, description= 'Preferred transport mode.')
    must_avoid: Optional[List[str]] = Field(default = None, description= 'Thing to avoid (e.g., museum)')
    
    
class DeliveryOption(BaseModel):
    send_email: bool = Field(default = False, description= ' If true, send itinerary + event info via email')
    email: Optional[EmailStr] = Field(default= None, description= ' Email address for delivery (required if send_email = True)')
    language: Language = Field(default = Language.en, description= ' Preferred language for the report and user output.')

    @model_validator(mode = 'after')
    def validate_email(self):
        if self.send_email and not self.email:
            raise ValueError('Delivery Options email is required when send_email = True')
        return self


# Top Level User Request
class SightseeingPreferences(BaseModel):
    interests: Optional[str] = Field(default = None, description= 'Desired sightseeing interests, e.g. landmarks, viewpoints, history.')
    indoor_outdoor: Optional[str] = Field(default = None, description= ' Indoor, Outdoor, or mixed preferences.')
    free_only: bool = Field(default = None, description= ' If ture prefer free sightseeing spots.')


class UserRequest(BaseModel):
    """ Top Level request object that UI will create and pass to the agent"""
    
    user: UserProfile = Field(default_factory= UserProfile)
    trip: TripRequest
    events: EventPreferences = Field(default_factory= EventPreferences)
    sightseeing : Optional[SightseeingPreferences] = None
    itinerary: ItineraryPreferences = Field(default_factory= ItineraryPreferences)
    delivery: Optional[DeliveryOption] = Field(default= None)


# Structured Outputs

class Money(BaseModel):
    """ 
    Money representation
    """
    amount_eur: Optional[confloat(ge=0)] = Field(default = None, description= 'Amount in EUR (integer)')
    display: Optional[str] = Field(default = None, description= 'Original price text, e-g from 15€, free, 12€-18€')
    
    
class Source(BaseModel):
    url: str = Field(description= 'Source URL used to extract/verify information.')
    label: Optional[str] = Field(default = None, description= 'Human readable label, e.g. Event listing')
    retrieved_at: Optional[str] = Field(default = None, description= 'ISO datetime when source was retrieved')
    
    
class EventItem(BaseModel):
    name: str = Field(description= 'Event name.')
    start_datetime: Optional[str] = Field(default = None, description= 'Event start datetime')
    end_datetime: Optional[str] = Field(default = None, description= 'Event end datetime')
    address_or_area: Optional[str] = Field(default = None, description= 'Address or area district')
    price: Optional[Money] = Field(default = None, description= 'Ticket price if known.')
    description: Optional[str] = Field(default = None, description= 'Short event description(from source).')
    category_tags: Optional[List[str]] = Field(default = None, description= 'Tags/categories.')
    source_url: str = Field(description= 'Primary info URL for the event. If only one URL is available, set it to the ticket URL.')
    ticket_url: Optional[str] = Field(default = None, description = 'Ticket / booking URL (e.g. ticketShopUrl).')
    event_id: str = Field(description= 'Backend event ID, used to fetch similar events and to uniquely identify the event')
    
    
class SightseeingSpot(BaseModel):
    name: str = Field(description= 'Sight/POI name.')
    area_or_district: Optional[str] = Field(description= 'Area or district')
    address: str = Field(description= 'Address should be provided')
    entry_fee: Optional[Money] = Field(default = None, description= 'Entry fee if known')
    opening_hours: Optional[str] = Field(default = None, description= 'Opening hours if known')
    why_visit: str = Field(description= '1-2 sentences reason why it matches user request.')
    source_url: str = Field(description= ' Primary URL for this spot (required for prototype)')
    
    
class FoodDrinkSpot(BaseModel):
    name: str = Field(description= 'Venue name.')
    venue_type: Literal['restaurant', 'bar', 'cafe', 'other'] = Field(description= 'Venue category.')
    area_or_district: Optional[str] = Field(default = None, description= 'Area or district')
    address: Optional[str] = Field(default = None, description= 'Venue address if known')
    price_hint: Optional[str] = Field(default = None, description= 'Short price hint if known, e.g. cocktails 14-18 EUR')
    opening_hours: Optional[str] = Field(default = None, description= 'Opening hours if known')
    why_match: str = Field(description= '1-2 sentences why this venue matches the user request.')
    source_url: str = Field(description= 'Primary source URL for this venue.')


class ItineraryStop(BaseModel):
    stop_type: Literal['sightseeing', 'event', 'food', 'other'] = Field(description= 'type of stop')
    title: str = Field(description= 'Display title of the stop')
    start_time: Optional[str] = Field(default = None, description= 'Suggested start time (e.g. 10:30).')
    notes: Optional[str] = Field(default = None, description= 'Short note (booking tip, why placed here, etc.).')
    linked_item_name: Optional[str] = Field(default = None, description= 'Referenced event or place name.')
    source_url: Optional[str] = Field(default = None, description= 'Referenced source URL.')
    
    
class ItineraryDay(BaseModel):
    day_label: str = Field(description= 'Day label, e.g. Day 1 or 2026-01-23.')
    stops: List[ItineraryStop] = Field(description= 'Ordered list of stops for this day.')

    @model_validator(mode = "after")
    def validate_max_5_sightseeing(self):
        sightseeing_count = sum(1 for s in self.stops if s.stop_type == 'sightseeing')
        if sightseeing_count > 5:
            raise ValueError('ItineraryDay may contain at most 5 sightseeing stops.')
        return self
    
    
class Recommendation(BaseModel):
    """
    Store recommendation as a list of sentences to enforce the 'max 5 sentences' guardrail.
    """
    sentences: List[str] = Field(description= 'Recommendation sentences (max 5).')

    @model_validator(mode = "after")
    def validate_max_5(self):
        if len(self.sentences) > 5:
            raise ValueError('Recommendation must contain at most 5 sentences.')
        return self


class CoreResult(BaseModel):
    """
    Full, detailed result from the agent.
    """
    recommendation: Recommendation
    events: List[EventItem] = Field(default_factory=list, description= 'Up to 5 suggested events total.')
    sightseeing_spots: List[SightseeingSpot] = Field(default_factory=list, description= 'All sightseeing spots used in itinerary.')
    food_and_drink_spots: List[FoodDrinkSpot] = Field(default_factory=list, description= 'Concrete restaurants, bars, cafes, or other food/drink venues.')
    itinerary: List[ItineraryDay] = Field(default_factory=list, description= 'Day by day itinerary.')
    sources: List[Source] = Field(default_factory=list, description= 'All sources used (preferably deduplicated).')
    warnings: List[str] = Field(default_factory=list, description= 'Missing data warnings (prices not found, etc.).')

    @model_validator(mode="after")
    def validate_max_5_events(self):
        if len(self.events) > 5:
            raise ValueError('CoreResult.events may contain at most 5 events.')
        return self


class MarkdownSection(BaseModel):
    heading: str = Field(description= "Section heading, e.g. 'Events'.")
    body_markdown: str = Field(description= 'Markdown content for this section.')


class MarkdownReport(BaseModel):
    """
    Full report blueprint used for Markdown and email content.
    """
    title: str = Field(description= 'Report title.')
    recommendation: Recommendation
    sections: List[MarkdownSection] = Field(default_factory=list, description= 'Ordered report sections.')
    sources: List[Source] = Field(default_factory=list, description= 'Sources to show at the end.')
    created_at: Optional[str] = Field(default=None, description= 'ISO datetime when report was created.')


class ReporterResult(BaseModel):
    markdown_report: MarkdownReport
    saved_report_path: str = Field(description = 'Absolute path where the markdown report was saved.')


class UIEventTeaser(BaseModel):
    name: str
    start_datetime: Optional[str] = None
    venue_name: Optional[str] = None
    price_display: Optional[str] = None
    source_url: str
    ticket_url: Optional[str] = Field(default = None, description = 'Ticket / booking URL.')


class UISpotItem(BaseModel):
    name: str
    entry_fee_display: Optional[str] = None
    opening_hours: Optional[str] = None
    source_url: str

class UIItineraryStop(BaseModel):
    title: str
    start_time: Optional[str] = None
    notes: Optional[str] = None
    stop_type: Optional[str] = None
    linked_item_name: Optional[str] = None
    source_url: Optional[str] = None
    
    
class UIDayOverview(BaseModel):
    day_label: str
    stops: List[UIItineraryStop] = Field(description= "Ordered itinerary stops for UI display.")


class UIFoodDrinkSpot(BaseModel):
    name: str
    venue_type: str
    price_hint: Optional[str] = None
    opening_hours: Optional[str] = None
    source_url: str


class UIResult(BaseModel):
    """
    Short UI output:
    - Recommendation (max 5 sentences)
    - All sightseeing spots (short)
    - Only 2–3 events (hard limit: max 3)
    - Day 1 / Day 2 overview (and more days if trip longer)
    """
    recommendation: Recommendation
    top_events: List[UIEventTeaser] = Field(default_factory=list, description= '2–3 events for the UI.')
    sightseeing_spots: List[UISpotItem] = Field(default_factory=list, description= 'All sightseeing spots (short).')
    food_and_drink_spots: List[UIFoodDrinkSpot] = Field(default_factory=list, description= 'Concrete food and drink recommendations.')
    itinerary_overview: List[UIDayOverview] = Field(default_factory=list, description= 'Day overview.')
    warnings: List[str] = Field(default_factory=list)


    @model_validator(mode = 'after')
    def validate_max_3_top_events(self):
        if len(self.top_events) > 3:
            raise ValueError('UIResult.top_events may contain at most 3 events.')
        return self
    

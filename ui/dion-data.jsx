// Realistic data based on src/schemas.py + DEMO_CASES.md
// Available models from src/event_client.py AVAILABLE_MODELS
const AVAILABLE_MODELS = [
  'google/gemini-2.5-flash',
  'z-ai/glm-4.7',
  'moonshotai/kimi-k2.6',
  'anthropic/claude-haiku-4-5',
];
const DEFAULT_MODEL = AVAILABLE_MODELS[0];

const TIME_PREF = ['No preference', 'Daytime', 'Evening', 'Night'];
const PLANNING_MODES = ['Full Trip', 'Event or Day Trip'];
const SIGHTSEEING_MODES = ['No preference', 'Indoor', 'Outdoor', 'Mixed'];
const LANGUAGES = ['English', 'Deutsch'];
const GROUP_SIZES = Array.from({length:15}, (_,i)=> i+1);

// Demo result mirroring UIResult schema (city: Berlin, electronic vibe demo case)
const DEMO_PLAN = {
  request: {
    user: { name: 'Adriana' },
    trip: {
      city: 'Berlin', country: 'Germany',
      date_start: '2026-05-15', date_end: '2026-05-17',
      include_last_day: true, planning_mode: 'full_trip',
      events_enabled: true, sightseeing_enabled: true, food_drink_enabled: true,
      group_size: 2, budget: { min_budget: 200, max_budget: 600 }
    },
    events: { vibe: 'techno, underground', categories: 'club, concert', time_pref: 'night', free_only: false },
    sightseeing: { interests: 'street art, viewpoints, history', indoor_outdoor: 'mixed', free_only: false },
    itinerary: { must_avoid: ['museums', 'luxury dining'] },
    delivery: { send_email: false, language: 'English' }
  },
  recommendation: {
    sentences: [
      'Berlin in May rewards a slow start and a long, late night — pace yourself.',
      'Anchor the trip around Friday at Berghain and a softer Saturday in Friedrichshain.',
      'Prioritise rooftop drinks at Klunkerkranich for an unscripted golden hour.',
      'Skip touristy Mitte at peak hours; East Side Gallery is best at 9am.',
      "Two of the food picks are walk-ins only — book the Sunday brunch in advance."
    ]
  },
  top_events: [
    { name: 'Klockworks Showcase ft. Ben Klock', start_datetime: '2026-05-15T23:30:00+02:00',
      venue_name: 'Berghain', price_display: 'from 25.00 EUR', source_url: 'https://www.eventim.de/event/klockworks-berghain-1234567/' },
    { name: 'Modeselektor Live', start_datetime: '2026-05-16T22:00:00+02:00',
      venue_name: 'Säälchen Holzmarkt', price_display: 'from 38.00 EUR', source_url: 'https://www.eventim.de/event/modeselektor-saaelchen-7654321/' },
    { name: 'Sunday Klub Open Air', start_datetime: '2026-05-17T14:00:00+02:00',
      venue_name: 'about blank', price_display: 'from 18.00 EUR', source_url: 'https://www.eventim.de/event/about-blank-sunday-klub-9988776/' }
  ],
  sightseeing_spots: [
    { name: 'East Side Gallery', entry_fee_display: 'free', opening_hours: 'open 24h', source_url: 'https://www.eastsidegallery-berlin.de/' },
    { name: 'Klunkerkranich Rooftop', entry_fee_display: '5 EUR', opening_hours: 'Fr–So 14:00–24:00', source_url: 'https://klunkerkranich.org/' },
    { name: 'Tempelhofer Feld', entry_fee_display: 'free', opening_hours: 'sunrise to sunset', source_url: 'https://gruen-berlin.de/tempelhofer-feld' },
    { name: 'Reichstag Glaskuppel', entry_fee_display: 'free (Anmeldung)', opening_hours: '8:00–24:00', source_url: 'https://www.bundestag.de/besuche/kuppel' }
  ],
  food_and_drink_spots: [
    { name: 'Mogg Deli', venue_type: 'restaurant', price_hint: 'mains 14–22 EUR', opening_hours: 'Mi–So 12:00–22:00', source_url: 'https://moggandmelzer.com/' },
    { name: 'Buck and Breck', venue_type: 'bar', price_hint: 'cocktails 14–18 EUR', opening_hours: 'tgl. 19:00–02:00', source_url: 'https://buckandbreck.com/' },
    { name: 'Bonanza Coffee Heroes', venue_type: 'cafe', price_hint: '4–8 EUR', opening_hours: 'tgl. 9:30–18:00', source_url: 'https://bonanzacoffee.de/' },
    { name: 'Lode & Stijn', venue_type: 'restaurant', price_hint: 'tasting 65 EUR', opening_hours: 'Do–Sa 19:00–23:00', source_url: 'https://lode-stijn.de/' }
  ],
  itinerary_overview: [
    { day_label: '2026-05-15', stops: [
      { stop_type:'food', start_time:'10:00', title:'Coffee at Bonanza Coffee Heroes', notes:'Small Prenzlauer Berg roastery — relaxed start.', linked_item_name:'Bonanza Coffee Heroes' },
      { stop_type:'sightseeing', start_time:'11:30', title:'East Side Gallery walk', notes:'Best earlier in the day before the tour buses arrive.', linked_item_name:'East Side Gallery' },
      { stop_type:'food', start_time:'19:30', title:'Dinner at Mogg Deli', notes:'Set the mood before the late club night.', linked_item_name:'Mogg Deli' },
      { stop_type:'event', start_time:'23:30', title:'Klockworks Showcase ft. Ben Klock', notes:'Arrive between 1–3am for shorter line. Cash only.', linked_item_name:'Klockworks Showcase ft. Ben Klock' }
    ]},
    { day_label: '2026-05-16', stops: [
      { stop_type:'food', start_time:'12:30', title:'Brunch at Mogg Deli', notes:'Late wake-up assumed.', linked_item_name:'Mogg Deli' },
      { stop_type:'sightseeing', start_time:'15:00', title:'Klunkerkranich Rooftop', notes:'Stay through golden hour.', linked_item_name:'Klunkerkranich Rooftop' },
      { stop_type:'food', start_time:'18:30', title:'Drinks at Buck and Breck', notes:'Walk-in tip: arrive right at opening.', linked_item_name:'Buck and Breck' },
      { stop_type:'event', start_time:'22:00', title:'Modeselektor Live', notes:'Shorter format than a club night.', linked_item_name:'Modeselektor Live' }
    ]},
    { day_label: '2026-05-17', stops: [
      { stop_type:'sightseeing', start_time:'09:30', title:'Tempelhofer Feld stroll', notes:'Borrow a bike at the entrance.', linked_item_name:'Tempelhofer Feld' },
      { stop_type:'event', start_time:'14:00', title:'Sunday Klub Open Air', notes:'Closing slot only — leave by 22:00 for evening flight.', linked_item_name:'Sunday Klub Open Air' }
    ]}
  ],
  warnings: [
    'Eventim prices are synced once per day and may vary slightly later. Use the ticket link for the latest live pricing.',
    'No verified public link could be confirmed for: Buck and Breck. The place was kept, but its link was removed.'
  ],
  personal_feedback: [
    "I kept the Sunday lighter on purpose — three full club nights in a row burns most travellers out.",
    "If you skip Berghain on Friday, swap in 'Renate' which closed during my last refresh — let me know."
  ],
  saved_report_path: 'outputs/reports/2026-05-15_berlin_dion_plan.md',
  report_size_kb: 12.4
};

// Demo cases covering a wide range of scenarios, vibes, and edge cases
const DEMO_CASES = [
  {
    id: 'case1', label: 'Case 1 — Rock Weekend Düsseldorf (EN)',
    scope: { events:true, sightseeing:true, food:true },
    form: { user_name:'Chris', city:'Düsseldorf', country:'Germany', date_start:'2026-05-22', date_end:'2026-05-24', include_last_day:false, planning_mode:'Full Trip', group_size:2, min_budget:'120', max_budget:'350', vibe:'rock, indie, alternative', categories:'Concert, Live Music', time_pref:'Evening', free_only:false, sightseeing_interests:'Altstadt, Rheinufer, street art', sightseeing_mode:'Mixed', sightseeing_free_only:false, must_avoid:'Techno, Pop, Familienevents', user_notes:'', language:'English' }
  },
  {
    id: 'case2', label: 'Case 2 — Nur Food & Drinks Köln (DE)',
    scope: { events:false, sightseeing:false, food:true },
    form: { user_name:'Jonas', city:'Köln', country:'Germany', date_start:'2026-05-30', date_end:'2026-05-30', include_last_day:true, planning_mode:'Event or Day Trip', group_size:3, min_budget:'60', max_budget:'180', vibe:'', categories:'', time_pref:'Evening', free_only:false, sightseeing_interests:'', sightseeing_mode:'No preference', sightseeing_free_only:false, must_avoid:'Fast Food, Kettenrestaurants', user_notes:'Wir möchten den Abend mit guten Cocktails starten und danach schick essen gehen. Einer aus der Gruppe ist Vegetarier.', language:'Deutsch' }
  },
  {
    id: 'case3', label: 'Case 3 — Free-Budget Day Leipzig (EN)',
    scope: { events:true, sightseeing:true, food:false },
    form: { user_name:'', city:'Leipzig', country:'Germany', date_start:'2026-06-06', date_end:'2026-06-06', include_last_day:true, planning_mode:'Event or Day Trip', group_size:2, min_budget:'0', max_budget:'20', vibe:'indie, alternative, experimental', categories:'Free Concert, Open Air', time_pref:'Daytime', free_only:true, sightseeing_interests:'street art, parks, Karl-Marx-Platz', sightseeing_mode:'Outdoor', sightseeing_free_only:true, must_avoid:'paid clubs, expensive venues, nightlife', user_notes:'', language:'English' }
  },
  {
    id: 'case4', label: 'Case 4 — Minimale Eingabe Hamburg (DE)',
    scope: { events:true, sightseeing:true, food:true },
    form: { user_name:'', city:'Hamburg', country:'Germany', date_start:'2026-06-13', date_end:'2026-06-13', include_last_day:true, planning_mode:'Full Trip', group_size:2, min_budget:'', max_budget:'', vibe:'', categories:'', time_pref:'No preference', free_only:false, sightseeing_interests:'', sightseeing_mode:'No preference', sightseeing_free_only:false, must_avoid:'', user_notes:'', language:'Deutsch' }
  },
  {
    id: 'case5', label: 'Case 5 — Follow-Up Revision (basiert auf Case 1)',
    scope: { events:true, sightseeing:true, food:true },
    followup_message: 'Add a Sunday brunch spot, replace the Saturday dinner with something more upscale, and cut sightseeing down to max 2 stops.',
    form: { user_name:'Chris', city:'Düsseldorf', country:'Germany', date_start:'2026-05-22', date_end:'2026-05-24', include_last_day:false, planning_mode:'Full Trip', group_size:2, min_budget:'120', max_budget:'350', vibe:'rock, indie, alternative', categories:'Concert, Live Music', time_pref:'Evening', free_only:false, sightseeing_interests:'Altstadt, Rheinufer, street art', sightseeing_mode:'Mixed', sightseeing_free_only:false, must_avoid:'Techno, Pop, Familienevents', user_notes:'', language:'English' }
  },
];

window.DION_DATA = { AVAILABLE_MODELS, DEFAULT_MODEL, TIME_PREF, PLANNING_MODES, SIGHTSEEING_MODES, LANGUAGES, GROUP_SIZES, DEMO_PLAN, DEMO_CASES };

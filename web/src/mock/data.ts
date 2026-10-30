import type { HAArea, HALightEntity, ScheduledScenesConfig } from '../types'

export const MOCK_AREAS: HAArea[] = [
  { area_id: 'living_room', name: 'Living Room' },
  { area_id: 'kitchen', name: 'Kitchen' },
  { area_id: 'bedroom', name: 'Bedroom' },
  { area_id: 'office', name: 'Office' },
  { area_id: 'hallway', name: 'Hallway' },
]

export const MOCK_LIGHTS: HALightEntity[] = [
  // Living Room
  {
    entity_id: 'light.living_room_cove',
    name: 'Cove LED Strip',
    area_id: 'living_room',
    area_name: 'Living Room',
    state: 'on',
    supported_color_modes: ['color_temp'],
    min_color_temp_kelvin: 2000,
    max_color_temp_kelvin: 6500,
  },
  {
    entity_id: 'light.living_room_ceiling',
    name: 'Ceiling Downlights',
    area_id: 'living_room',
    area_name: 'Living Room',
    state: 'on',
    supported_color_modes: ['color_temp'],
    min_color_temp_kelvin: 2200,
    max_color_temp_kelvin: 5000,
  },
  {
    entity_id: 'light.living_room_floor_lamp',
    name: 'Reading Floor Lamp',
    area_id: 'living_room',
    area_name: 'Living Room',
    state: 'on',
    supported_color_modes: ['color_temp'],
    min_color_temp_kelvin: 2000,
    max_color_temp_kelvin: 4000,
  },
  {
    entity_id: 'light.living_room_accent',
    name: 'Artwork Spotlight',
    area_id: 'living_room',
    area_name: 'Living Room',
    state: 'off',
    supported_color_modes: ['brightness'],
    min_color_temp_kelvin: 2700,
    max_color_temp_kelvin: 2700,
  },

  // Kitchen
  {
    entity_id: 'light.kitchen_spots',
    name: 'Main Spotlights',
    area_id: 'kitchen',
    area_name: 'Kitchen',
    state: 'off',
    supported_color_modes: ['color_temp'],
    min_color_temp_kelvin: 2200,
    max_color_temp_kelvin: 5000,
  },
  {
    entity_id: 'light.kitchen_counter_strip',
    name: 'Counter Under-Cabinet Strip',
    area_id: 'kitchen',
    area_name: 'Kitchen',
    state: 'off',
    supported_color_modes: ['color_temp'],
    min_color_temp_kelvin: 2000,
    max_color_temp_kelvin: 6500,
  },
  {
    entity_id: 'light.kitchen_island_pendants',
    name: 'Island Pendants',
    area_id: 'kitchen',
    area_name: 'Kitchen',
    state: 'off',
    supported_color_modes: ['color_temp'],
    min_color_temp_kelvin: 1800,
    max_color_temp_kelvin: 4000,
  },

  // Bedroom
  {
    entity_id: 'light.bedroom_pendants',
    name: 'Bedside Pendants',
    area_id: 'bedroom',
    area_name: 'Bedroom',
    state: 'off',
    supported_color_modes: ['color_temp'],
    min_color_temp_kelvin: 1800,
    max_color_temp_kelvin: 3500,
  },
  {
    entity_id: 'light.bedroom_ceiling',
    name: 'Main Ceiling Fixture',
    area_id: 'bedroom',
    area_name: 'Bedroom',
    state: 'off',
    supported_color_modes: ['color_temp'],
    min_color_temp_kelvin: 2200,
    max_color_temp_kelvin: 4500,
  },

  // Office
  {
    entity_id: 'light.office_desk_lamp',
    name: 'Desk Task Lamp',
    area_id: 'office',
    area_name: 'Office',
    state: 'off',
    supported_color_modes: ['color_temp'],
    min_color_temp_kelvin: 2200,
    max_color_temp_kelvin: 6500,
  },
  {
    entity_id: 'light.office_wall_washers',
    name: 'Back Wall Washers',
    area_id: 'office',
    area_name: 'Office',
    state: 'off',
    supported_color_modes: ['color_temp'],
    min_color_temp_kelvin: 2000,
    max_color_temp_kelvin: 5000,
  },

  // Hallway
  {
    entity_id: 'light.hallway_nightlight',
    name: 'Hallway Recessed Light',
    area_id: 'hallway',
    area_name: 'Hallway',
    state: 'off',
    supported_color_modes: ['color_temp'],
    min_color_temp_kelvin: 1800,
    max_color_temp_kelvin: 3500,
  },
]

export const INITIAL_CONFIG: ScheduledScenesConfig = {
  curves: {
    gu10_warm_glow: {
      name: 'gu10_warm_glow',
      lights: ['light.living_room_ceiling', 'light.kitchen_spots'],
      points: [
        [1, 2200],
        [40, 2700],
        [100, 4000],
      ],
    },
    cove_ambient_led: {
      name: 'cove_ambient_led',
      lights: ['light.living_room_cove', 'light.kitchen_counter_strip'],
      points: [
        [1, 2000],
        [50, 2600],
        [100, 3500],
      ],
    },
    reading_warmth: {
      name: 'reading_warmth',
      lights: ['light.living_room_floor_lamp'],
      points: [
        [1, 1900],
        [30, 2200],
        [80, 2800],
        [100, 3200],
      ],
    },
  },
  brightness_curves: {
    living_room_accent: {
      name: 'living_room_accent',
      lights: ['light.living_room_cove'],
      points: [
        [0, 0],
        [50, 100],
        [100, 100],
      ],
    },
    living_room_main: {
      name: 'living_room_main',
      lights: ['light.living_room_ceiling'],
      points: [
        [0, 0],
        [30, 0],
        [50, 30],
        [100, 100],
      ],
    },
    kitchen_task: {
      name: 'kitchen_task',
      lights: ['light.kitchen_counter_strip'],
      points: [
        [0, 0],
        [20, 40],
        [60, 90],
        [100, 100],
      ],
    },
  },
  programs: [
    {
      name: 'living_room',
      lights: [
        'light.living_room_cove',
        'light.living_room_ceiling',
        'light.living_room_floor_lamp',
      ],
      transition_time: 120,
      transition_interval: 60,
      enable_when_light_turn_on: true,
      disable_when_lights_off: false,
      allow_turn_on_if_any_on: true,
      schedule: [
        {
          id: 'step-1',
          time: '06:30',
          brightness: 15,
          temp: 2200,
        },
        {
          id: 'step-2',
          time: '09:00',
          brightness: 100,
          temp: 5000,
        },
        {
          id: 'step-3',
          time: '16:30',
          brightness: 100,
          temp: 4500,
        },
        {
          id: 'step-4',
          time: '20:00',
          brightness: 50,
          temp: 2700,
        },
        {
          id: 'step-5',
          time: '23:30',
          brightness: 10,
          temp: 2000,
        },
      ],
    },
    {
      name: 'kitchen',
      lights: [
        'light.kitchen_spots',
        'light.kitchen_counter_strip',
        'light.kitchen_island_pendants',
      ],
      transition_time: 90,
      transition_interval: 60,
      enable_when_light_turn_on: true,
      disable_when_lights_off: false,
      allow_turn_on_if_any_on: true,
      schedule: [
        {
          id: 'kstep-1',
          time: '06:30',
          brightness: 20,
          temp: 2400,
        },
        {
          id: 'kstep-2',
          time: '08:30',
          brightness: 100,
          temp: 4500,
        },
        {
          id: 'kstep-3',
          time: '18:00',
          brightness: 80,
          temp: 3500,
        },
        {
          id: 'kstep-4',
          time: '22:00',
          brightness: 15,
          temp: 2200,
        },
      ],
    },
  ],
}

import React from 'react';

const buttonKinds = new Set(['ActionButton', 'ActionMenu', 'Button', 'CloseButton', 'DialogTrigger', 'FileTrigger', 'LinkButton', 'MenuTrigger', 'SubmenuTrigger', 'ToggleButton', 'TooltipTrigger', 'UnavailableMenuItemTrigger']);
const fieldKinds = new Set(['Autocomplete', 'ColorField', 'ComboBox', 'DateField', 'DatePicker', 'DateRangePicker', 'NumberField', 'Picker', 'SearchField', 'TextField', 'TimeField']);
const calendarKinds = new Set(['Calendar', 'RangeCalendar']);
const cardKinds = new Set(['AssetCard', 'Card', 'CardPreview', 'CollectionCardPreview', 'ProductCard', 'UserCard']);
const collectionKinds = new Set(['Collection', 'ListView', 'TableView', 'TreeView']);
const overlayKinds = new Set(['AlertDialog', 'ContextualHelp', 'ContextualHelpPopover', 'CustomDialog', 'Dialog', 'DialogContainer', 'FullscreenDialog', 'InlineAlert', 'Popover', 'ToastContainer', 'ToastQueue', 'Tooltip']);

function labelFor(kind, props) {
  return props.children || props.label || kind.replace(/([a-z0-9])([A-Z])/g, '$1 $2');
}

function calendar(kind, props) {
  const days = ['M', 'T', 'W', 'T', 'F', 'S', 'S', '29', '30', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
  return React.createElement('section', {className: 's2d-calendar', 'aria-label': props['aria-label'] || kind},
    React.createElement('header', null, React.createElement('button', {type: 'button'}, 'Prev'), React.createElement('strong', null, kind === 'RangeCalendar' ? 'April – May 2026' : 'April 2026'), React.createElement('button', {type: 'button'}, 'Next')),
    React.createElement('div', {className: 's2d-calendar-grid'}, days.map((day, index) => React.createElement('span', {className: index === 12 ? 'is-selected' : index < 7 ? 'is-weekday' : '', key: index}, day)))
  );
}

function card(kind, props) {
  return React.createElement('article', {className: 's2d-card'},
    React.createElement('div', {className: 's2d-card-preview'}, kind.includes('User') ? 'U' : kind.includes('Product') ? 'P' : 'S2'),
    React.createElement('strong', null, labelFor(kind, props)),
    React.createElement('span', null, props.description || 'Adaptive Spectrum 2 content'));
}

function collection(kind, props) {
  const label = labelFor(kind, props);
  if (kind === 'TableView') {
    return React.createElement('table', {className: 's2d-table'}, React.createElement('thead', null, React.createElement('tr', null, React.createElement('th', null, 'Name'), React.createElement('th', null, 'Status'))), React.createElement('tbody', null, React.createElement('tr', null, React.createElement('td', null, 'Concept.fig'), React.createElement('td', null, 'Ready')), React.createElement('tr', null, React.createElement('td', null, 'Review.pdf'), React.createElement('td', null, 'Shared'))));
  }
  return React.createElement('section', {className: 's2d-collection'}, React.createElement('strong', null, label), React.createElement('div', {className: 'is-selected'}, 'Selected item'), React.createElement('div', null, 'Second item'), React.createElement('div', null, 'Third item'));
}

function overlay(kind, props) {
  return React.createElement('section', {className: 's2d-overlay'}, React.createElement('strong', null, labelFor(kind, props)), React.createElement('p', null, props.description || 'A concise message with a clear next action.'), React.createElement('div', {className: 's2d-inline-actions'}, React.createElement('button', {className: 's2d-button s2d-button-secondary', type: 'button'}, 'Cancel'), React.createElement('button', {className: 's2d-button s2d-button-accent', type: 'button'}, 'Confirm')));
}

export function renderS2Component(kind, props = {}) {
  const label = labelFor(kind, props);
  const disabled = Boolean(props.isDisabled);
  if (buttonKinds.has(kind)) {
    const variant = props.variant || (kind === 'Button' || kind === 'LinkButton' ? 'accent' : 'secondary');
    const Element = kind === 'LinkButton' ? 'a' : 'button';
    return React.createElement(Element, {className: `s2d-button s2d-button-${variant}`, disabled, href: Element === 'a' ? '#' : undefined, onClick: props.onPress, type: Element === 'button' ? 'button' : undefined}, label);
  }
  if (['ActionBar', 'ActionButtonGroup', 'ButtonGroup', 'ToggleButtonGroup'].includes(kind)) {
    return React.createElement('div', {className: 's2d-inline-actions'}, React.createElement('button', {className: 's2d-button s2d-button-secondary', type: 'button'}, 'Edit'), React.createElement('button', {className: 's2d-button s2d-button-secondary', type: 'button'}, 'Share'), React.createElement('button', {className: 's2d-button s2d-button-quiet', type: 'button'}, 'More'));
  }
  if (['Checkbox', 'Radio', 'Switch'].includes(kind)) {
    const inputType = kind === 'Radio' ? 'radio' : 'checkbox';
    return React.createElement('label', {className: `s2d-choice s2d-choice-${kind.toLowerCase()}`}, React.createElement('input', {type: inputType, defaultChecked: props.isSelected !== false, disabled}), React.createElement('span', null), React.createElement('b', null, label));
  }
  if (kind === 'CheckboxGroup' || kind === 'RadioGroup') {
    const inputType = kind === 'RadioGroup' ? 'radio' : 'checkbox';
    return React.createElement('fieldset', {className: 's2d-choice-group'}, React.createElement('legend', null, label), ['First option', 'Second option'].map((item, index) => React.createElement('label', {className: 's2d-choice', key: item}, React.createElement('input', {type: inputType, name: kind, defaultChecked: index === 0}), React.createElement('span', null), React.createElement('b', null, item))));
  }
  if (fieldKinds.has(kind)) {
    const fieldType = kind === 'SearchField' ? 'search' : kind === 'NumberField' ? 'number' : 'text';
    return React.createElement('label', {className: 's2d-field'}, React.createElement('span', null, label), React.createElement('div', {className: 's2d-field-shell'}, React.createElement('input', {type: fieldType, defaultValue: props.value || (kind.includes('Date') ? 'Apr 15, 2026' : 'Spectrum 2 value'), disabled}), React.createElement('button', {type: 'button', tabIndex: -1}, kind === 'SearchField' ? 'Clear' : 'Open')));
  }
  if (kind === 'TextArea') return React.createElement('label', {className: 's2d-field'}, React.createElement('span', null, label), React.createElement('textarea', {defaultValue: props.value || 'Write a clear description.', disabled}));
  if (kind === 'Form') return React.createElement('form', {className: 's2d-form'}, React.createElement('label', {className: 's2d-field'}, React.createElement('span', null, 'Project name'), React.createElement('input', {defaultValue: 'Spectrum 2 project'})), React.createElement('button', {className: 's2d-button s2d-button-accent', type: 'button'}, 'Save'));
  if (kind === 'DropZone') return React.createElement('div', {className: 's2d-dropzone'}, React.createElement('strong', null, 'Drop files here'), React.createElement('span', null, 'or choose from your computer'));
  if (kind === 'Slider' || kind === 'RangeSlider') return React.createElement('label', {className: 's2d-slider'}, React.createElement('span', null, label), React.createElement('input', {type: 'range', min: 0, max: 100, defaultValue: kind === 'RangeSlider' ? 68 : 42}));
  if (calendarKinds.has(kind)) return calendar(kind, props);
  if (kind.startsWith('Color')) {
    if (kind === 'ColorSwatch') return React.createElement('div', {className: 's2d-color-swatch', title: 'rgb(59, 99, 251)'});
    if (kind === 'ColorSwatchPicker') return React.createElement('div', {className: 's2d-swatches'}, ['#3b63fb', '#e34850', '#2d9d78', '#f0a30a', '#9b55d9'].map(color => React.createElement('button', {key: color, style: {background: color}, title: color, type: 'button'})));
    return React.createElement('section', {className: `s2d-color-control s2d-color-${kind.toLowerCase()}`}, React.createElement('div', null), React.createElement('code', null, 'rgb(59, 99, 251)'));
  }
  if (kind === 'ProgressBar' || kind === 'Meter') return React.createElement('label', {className: 's2d-progress'}, React.createElement('span', null, label, ' · 68%'), React.createElement('progress', {max: 100, value: 68}));
  if (kind === 'ProgressCircle') return React.createElement('div', {className: 's2d-progress-circle'}, React.createElement('span', null, '68'));
  if (kind === 'StatusLight') return React.createElement('span', {className: 's2d-status'}, React.createElement('i', null), label);
  if (kind === 'Badge' || kind === 'NotificationBadge') return React.createElement('span', {className: kind === 'Badge' ? 's2d-badge' : 's2d-notification-badge'}, kind === 'NotificationBadge' ? '3' : label);
  if (kind === 'Avatar' || kind === 'AvatarGroup') return React.createElement('div', {className: 's2d-avatar-group'}, React.createElement('div', {className: 's2d-avatar'}, 'S2'), kind === 'AvatarGroup' ? React.createElement('div', {className: 's2d-avatar'}, 'UI') : null);
  if (cardKinds.has(kind)) return card(kind, props);
  if (kind === 'CardView') return React.createElement('div', {className: 's2d-card-view'}, card('Card', {label: 'First'}), card('Card', {label: 'Second'}));
  if (collectionKinds.has(kind)) return collection(kind, props);
  if (kind === 'Breadcrumbs') return React.createElement('nav', {className: 's2d-breadcrumbs'}, React.createElement('a', {href: '#'}, 'Home'), React.createElement('span', null, '/'), React.createElement('a', {href: '#'}, 'Assets'), React.createElement('span', null, '/'), React.createElement('strong', null, 'Current'));
  if (kind === 'Accordion' || kind === 'Disclosure') return React.createElement('div', {className: 's2d-disclosure'}, React.createElement('strong', null, label), React.createElement('p', null, 'Expanded Spectrum 2 content.'));
  if (['Tabs', 'TabList', 'TabPanel', 'SegmentedControl'].includes(kind)) return React.createElement('section', {className: 's2d-tabs'}, React.createElement('div', null, React.createElement('button', {className: 'is-selected', type: 'button'}, 'Design'), React.createElement('button', {type: 'button'}, 'Code')), React.createElement('p', null, 'Selected content'));
  if (kind === 'TagGroup') return React.createElement('div', {className: 's2d-tags'}, React.createElement('span', null, 'Design'), React.createElement('span', null, 'Review'), React.createElement('span', null, 'Ready'));
  if (kind === 'SideNav') return React.createElement('nav', {className: 's2d-sidenav'}, React.createElement('strong', null, label), React.createElement('a', {className: 'is-selected', href: '#'}, 'Overview'), React.createElement('a', {href: '#'}, 'Assets'));
  if (kind === 'Menu') return React.createElement('div', {className: 's2d-menu'}, React.createElement('div', null, 'Open'), React.createElement('div', {className: 'is-selected'}, 'Share'), React.createElement('div', null, 'Download'));
  if (overlayKinds.has(kind)) return overlay(kind, props);
  if (kind === 'Skeleton' || kind === 'SkeletonCollection') return React.createElement('div', {className: 's2d-skeleton'}, React.createElement('span', null), React.createElement('span', null), React.createElement('span', null));
  if (kind === 'Divider') return React.createElement('hr', {className: 's2d-divider'});
  if (kind === 'Heading') return React.createElement('h3', {className: 's2d-heading'}, label);
  if (kind === 'Text') return React.createElement('p', {className: 's2d-text'}, label);
  if (kind === 'Keyboard') return React.createElement('kbd', {className: 's2d-keyboard'}, 'Cmd K');
  if (kind === 'Link') return React.createElement('a', {className: 's2d-link', href: '#'}, label);
  if (kind === 'Image' || kind === 'IllustratedMessage') return React.createElement('div', {className: 's2d-media'}, React.createElement('div', {className: 's2d-media-shape'}, kind === 'Image' ? 'Image' : 'Message'), React.createElement('strong', null, label));
  if (kind === 'LabeledValue') return React.createElement('dl', {className: 's2d-labeled-value'}, React.createElement('dt', null, label), React.createElement('dd', null, props.value || 'Spectrum 2 value'));
  if (kind === 'Provider') return React.createElement('div', {className: 's2d-provider'}, 'Adaptive light · dark · touch');
  if (kind === 'CenterBaseline') return React.createElement('div', {className: 's2d-baseline'}, React.createElement('span', null, 'Aa'), React.createElement('span', null, '20'));
  return React.createElement('div', {className: 's2d-structural'}, React.createElement('strong', null, label), React.createElement('span', null, 'Composable S2 part'));
}

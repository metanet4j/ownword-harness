import React from 'react';

const buttonKinds = new Set(['ActionButton', 'ActionMenu', 'Button', 'FileTrigger', 'LogicButton', 'MenuTrigger', 'SubmenuTrigger', 'ToggleButton', 'TooltipTrigger', 'ContextualHelpTrigger', 'DialogTrigger']);
const fieldKinds = new Set(['ColorField', 'ComboBox', 'DateField', 'DatePicker', 'DateRangePicker', 'NumberField', 'Picker', 'SearchField', 'TextField', 'TimeField']);
const calendarKinds = new Set(['Calendar', 'RangeCalendar']);
const collectionKinds = new Set(['Accordion', 'Breadcrumbs', 'Collection', 'ListBox', 'ListView', 'Menu', 'TableBody', 'TableHeader', 'TableView', 'TagGroup', 'TreeView']);
const overlayKinds = new Set(['AlertDialog', 'ContextualHelp', 'Dialog', 'DialogContainer', 'InlineAlert', 'ToastContainer', 'ToastQueue', 'Tooltip']);

function labelFor(kind, props) {
  return props.children || props.label || kind.replace(/([a-z0-9])([A-Z])/g, '$1 $2');
}

function calendar(kind, props) {
  const days = ['M', 'T', 'W', 'T', 'F', 'S', 'S', '29', '30', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
  return React.createElement('section', {className: 'rsp3-calendar', 'aria-label': props['aria-label'] || kind},
    React.createElement('header', null, React.createElement('button', {type: 'button'}, '‹'), React.createElement('strong', null, kind === 'RangeCalendar' ? 'April – May 2026' : 'April 2026'), React.createElement('button', {type: 'button'}, '›')),
    React.createElement('div', {className: 'rsp3-calendar-grid'}, days.map((day, index) => React.createElement('span', {className: index === 12 ? 'is-selected' : index < 7 ? 'is-weekday' : '', key: index}, day)))
  );
}

function collection(kind, props) {
  const label = labelFor(kind, props);
  if (kind === 'Breadcrumbs') {
    return React.createElement('nav', {className: 'rsp3-breadcrumbs'}, React.createElement('a', {href: '#'}, 'Home'), React.createElement('span', null, '/'), React.createElement('a', {href: '#'}, 'Assets'), React.createElement('span', null, '/'), React.createElement('strong', null, 'Current'));
  }
  if (kind === 'Accordion') {
    return React.createElement('div', {className: 'rsp3-accordion'}, React.createElement('div', null, '▾  Details'), React.createElement('p', null, 'Expanded Spectrum content.'));
  }
  if (kind === 'TableView' || kind === 'TableHeader' || kind === 'TableBody') {
    return React.createElement('table', {className: 'rsp3-table'}, React.createElement('thead', null, React.createElement('tr', null, React.createElement('th', null, 'Name'), React.createElement('th', null, 'Status'))), React.createElement('tbody', null, React.createElement('tr', null, React.createElement('td', null, 'Asset.psd'), React.createElement('td', null, 'Ready')), React.createElement('tr', null, React.createElement('td', null, 'Review.pdf'), React.createElement('td', null, 'Shared'))));
  }
  return React.createElement('section', {className: 'rsp3-collection'}, React.createElement('strong', null, label), React.createElement('div', {className: 'is-selected'}, 'Selected item'), React.createElement('div', null, 'Second item'), React.createElement('div', null, 'Third item'));
}

function overlay(kind, props) {
  return React.createElement('section', {className: 'rsp3-overlay'}, React.createElement('strong', null, labelFor(kind, props)), React.createElement('p', null, props.description || 'Clear, concise supporting message.'), React.createElement('div', {className: 'rsp3-inline-actions'}, React.createElement('button', {className: 'rsp3-button rsp3-button-secondary', type: 'button'}, 'Cancel'), React.createElement('button', {className: 'rsp3-button rsp3-button-accent', type: 'button'}, 'Confirm')));
}

export function renderSpectrumComponent(kind, props = {}) {
  const label = labelFor(kind, props);
  const disabled = Boolean(props.isDisabled);
  const press = props.onPress;

  if (buttonKinds.has(kind)) {
    const variant = props.variant || (kind === 'Button' ? 'accent' : 'secondary');
    return React.createElement('button', {className: `rsp3-button rsp3-button-${variant}`, disabled, onClick: press, type: 'button'}, label);
  }
  if (kind === 'ActionBar' || kind === 'ActionBarContainer' || kind === 'ActionGroup' || kind === 'ButtonGroup') {
    return React.createElement('div', {className: 'rsp3-inline-actions'}, React.createElement('button', {className: 'rsp3-button rsp3-button-secondary', type: 'button'}, 'Edit'), React.createElement('button', {className: 'rsp3-button rsp3-button-secondary', type: 'button'}, 'Share'), React.createElement('button', {className: 'rsp3-button rsp3-button-quiet', type: 'button'}, 'More'));
  }
  if (kind === 'Checkbox' || kind === 'Radio' || kind === 'Switch') {
    const inputType = kind === 'Radio' ? 'radio' : 'checkbox';
    return React.createElement('label', {className: `rsp3-choice rsp3-choice-${kind.toLowerCase()}`}, React.createElement('input', {type: inputType, defaultChecked: props.isSelected !== false, disabled}), React.createElement('span', null), React.createElement('b', null, label));
  }
  if (kind === 'CheckboxGroup' || kind === 'RadioGroup') {
    const inputType = kind === 'RadioGroup' ? 'radio' : 'checkbox';
    return React.createElement('fieldset', {className: 'rsp3-choice-group'}, React.createElement('legend', null, label), ['First option', 'Second option'].map((item, index) => React.createElement('label', {className: 'rsp3-choice', key: item}, React.createElement('input', {type: inputType, name: kind, defaultChecked: index === 0}), React.createElement('span', null), React.createElement('b', null, item))));
  }
  if (fieldKinds.has(kind)) {
    const fieldType = kind === 'SearchField' ? 'search' : kind === 'NumberField' ? 'number' : 'text';
    return React.createElement('label', {className: 'rsp3-field'}, React.createElement('span', null, label), React.createElement('div', {className: 'rsp3-field-shell'}, React.createElement('input', {type: fieldType, defaultValue: props.value || (kind.includes('Date') ? 'Apr 15, 2026' : 'Spectrum value'), disabled}), React.createElement('button', {type: 'button', tabIndex: -1}, kind === 'SearchField' ? '×' : '⌄')));
  }
  if (kind === 'TextArea') {
    return React.createElement('label', {className: 'rsp3-field'}, React.createElement('span', null, label), React.createElement('textarea', {defaultValue: props.value || 'Write a clear description.', disabled}));
  }
  if (kind === 'Form') {
    return React.createElement('form', {className: 'rsp3-form'}, React.createElement('label', {className: 'rsp3-field'}, React.createElement('span', null, 'Project name'), React.createElement('input', {defaultValue: 'Spectrum project'})), React.createElement('label', {className: 'rsp3-choice'}, React.createElement('input', {type: 'checkbox', defaultChecked: true}), React.createElement('span', null), React.createElement('b', null, 'Send updates')), React.createElement('button', {className: 'rsp3-button rsp3-button-accent', type: 'button'}, 'Save'));
  }
  if (kind === 'DropZone') {
    return React.createElement('div', {className: 'rsp3-dropzone'}, React.createElement('strong', null, 'Drop files here'), React.createElement('span', null, 'or choose from your computer'));
  }
  if (kind === 'Slider' || kind === 'RangeSlider') {
    return React.createElement('label', {className: 'rsp3-slider'}, React.createElement('span', null, label), React.createElement('input', {type: 'range', min: 0, max: 100, defaultValue: kind === 'RangeSlider' ? 64 : 42}));
  }
  if (calendarKinds.has(kind)) {
    return calendar(kind, props);
  }
  if (kind.startsWith('Color')) {
    if (kind === 'ColorSwatch') {
      return React.createElement('div', {className: 'rsp3-color-swatch', title: '#0265DC'});
    }
    if (kind === 'ColorSwatchPicker') {
      return React.createElement('div', {className: 'rsp3-swatches'}, ['#0265dc', '#d31510', '#007a4d', '#b14c00', '#5c5ce0'].map(color => React.createElement('button', {key: color, style: {background: color}, title: color, type: 'button'})));
    }
    return React.createElement('section', {className: `rsp3-color-control rsp3-color-${kind.toLowerCase()}`}, React.createElement('div', null), React.createElement('code', null, '#0265DC'));
  }
  if (kind === 'ProgressBar' || kind === 'Meter') {
    return React.createElement('label', {className: 'rsp3-progress'}, React.createElement('span', null, label, ' · 64%'), React.createElement('progress', {max: 100, value: 64}));
  }
  if (kind === 'ProgressCircle') {
    return React.createElement('div', {className: 'rsp3-progress-circle'}, React.createElement('span', null, '64'));
  }
  if (kind === 'StatusLight') {
    return React.createElement('span', {className: 'rsp3-status'}, React.createElement('i', null), label);
  }
  if (kind === 'Badge') {
    return React.createElement('span', {className: 'rsp3-badge'}, label);
  }
  if (kind === 'Avatar') {
    return React.createElement('div', {className: 'rsp3-avatar', 'aria-label': props['aria-label'] || 'Avatar'}, 'RS');
  }
  if (kind === 'Divider') {
    return React.createElement('hr', {className: 'rsp3-divider'});
  }
  if (kind === 'Heading') {
    return React.createElement('h3', {className: 'rsp3-heading'}, label);
  }
  if (kind === 'Text') {
    return React.createElement('p', {className: 'rsp3-text'}, label);
  }
  if (kind === 'Keyboard') {
    return React.createElement('kbd', {className: 'rsp3-keyboard'}, '⌘ K');
  }
  if (kind === 'Link') {
    return React.createElement('a', {className: 'rsp3-link', href: '#'}, label);
  }
  if (kind === 'Image' || kind === 'IllustratedMessage') {
    return React.createElement('div', {className: 'rsp3-media'}, React.createElement('div', {className: 'rsp3-media-shape'}, kind === 'Image' ? 'Image' : '!'), React.createElement('strong', null, label));
  }
  if (kind === 'Icon') {
    return React.createElement('span', {className: 'rsp3-icon', 'aria-label': props['aria-label'] || 'Icon'}, '●');
  }
  if (kind === 'LabeledValue') {
    return React.createElement('dl', {className: 'rsp3-labeled-value'}, React.createElement('dt', null, label), React.createElement('dd', null, props.value || 'Spectrum value'));
  }
  if (kind === 'Well') {
    return React.createElement('div', {className: 'rsp3-well'}, label);
  }
  if (kind === 'Flex' || kind === 'Grid') {
    return React.createElement('div', {className: kind === 'Grid' ? 'rsp3-grid' : 'rsp3-flex'}, React.createElement('span', null, 'A'), React.createElement('span', null, 'B'), React.createElement('span', null, 'C'));
  }
  if (['Content', 'Footer', 'Header', 'Provider', 'SSRProvider', 'View', 'VisuallyHidden'].includes(kind)) {
    return React.createElement(kind === 'Footer' ? 'footer' : kind === 'Header' ? 'header' : 'section', {className: 'rsp3-surface'}, label);
  }
  if (collectionKinds.has(kind)) {
    return collection(kind, props);
  }
  if (['Tabs', 'TabList', 'TabPanels'].includes(kind)) {
    return React.createElement('section', {className: 'rsp3-tabs'}, React.createElement('div', null, React.createElement('button', {className: 'is-selected', type: 'button'}, 'Design'), React.createElement('button', {type: 'button'}, 'Code')), React.createElement('p', null, 'Selected tab content'));
  }
  if (['Disclosure', 'DisclosurePanel', 'DisclosureTitle', 'Item', 'Section', 'Column', 'Row', 'Cell', 'TreeViewItem', 'TreeViewItemContent'].includes(kind)) {
    return React.createElement('div', {className: 'rsp3-structural'}, React.createElement('strong', null, label), React.createElement('span', null, 'Composable collection part'));
  }
  if (overlayKinds.has(kind)) {
    return overlay(kind, props);
  }

  return React.createElement('div', {className: 'rsp3-surface'}, label);
}

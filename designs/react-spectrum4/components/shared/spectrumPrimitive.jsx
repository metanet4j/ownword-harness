import React from 'react';

const buttonKinds = new Set(['Button', 'ActionButton', 'ToggleButton']);
const fieldKinds = new Set(['TextField', 'NumberField', 'SearchField', 'Picker', 'ComboBox']);
const choiceKinds = new Set(['Checkbox', 'Radio', 'Switch']);
const groupKinds = new Set(['CheckboxGroup', 'RadioGroup']);

function labelFor(kind, props) {
  return props.children || props.label || kind.replace(/([a-z0-9])([A-Z])/g, '$1 $2');
}

function sizeClass(props) {
  return props.size && ['S', 'L'].includes(props.size) ? ` s2-size-${props.size}` : '';
}

function button(kind, props) {
  const variant = props.variant || 'primary';
  const fillStyle = props.fillStyle || 'fill';
  const isQuiet = props.isQuiet;
  let styleClass;
  if (isQuiet || (kind === 'ActionButton' && !props.isSelected)) styleClass = 's2-button-quiet';
  else if (fillStyle === 'outline' || variant === 'secondary') styleClass = 's2-button-outline';
  else if (variant === 'negative') styleClass = 's2-button-fill-negative';
  else if (variant === 'primary' || variant === 'accent') styleClass = 's2-button-fill-accent';
  else styleClass = 's2-button-fill-neutral';
  const classes = ['s2-button', styleClass];
  if (kind === 'ActionButton') classes.push('s2-button-icon');
  if (props.isSelected) classes.push('is-selected');
  if (props.isDisabled) classes.push('is-disabled');
  if (props.size) classes.push(`s2-button-size-${props.size}`);
  const glyph = kind === 'ActionButton' ? (props.isSelected ? '✓' : '＋') : kind === 'ToggleButton' ? (props.isSelected ? '★' : '☆') : '';
  return React.createElement('button', {className: classes.join(' '), type: 'button', disabled: Boolean(props.isDisabled), onClick: props.onPress}, glyph, labelFor(kind, props));
}

function choice(kind, props) {
  const inputType = kind === 'Switch' || kind === 'Checkbox' ? 'checkbox' : 'radio';
  const isSwitch = kind === 'Switch';
  return React.createElement('label', {className: `s2-choice${isSwitch ? ' s2-choice-switch' : kind === 'Radio' ? ' s2-choice-radio' : ''}`},
    React.createElement('input', {type: inputType, defaultChecked: props.isSelected !== false, disabled: Boolean(props.isDisabled)}),
    React.createElement('span', null),
    React.createElement('b', {style: {fontWeight: 500}}, labelFor(kind, props))
  );
}

function field(kind, props) {
  const inputType = kind === 'SearchField' ? 'search' : kind === 'NumberField' ? 'number' : 'text';
  const placeholder = props.placeholder || (kind === 'SearchField' ? 'Search' : '');
  const value = props.value ?? (kind === 'NumberField' ? '42' : kind === 'Picker' ? 'Select option' : kind === 'ComboBox' ? 'Spectrum value' : 'Spectrum value');
  const isPicker = kind === 'Picker' || kind === 'ComboBox';
  const isQuiet = props.isQuiet;
  const shellChildren = [React.createElement('input', {key: 'i', type: inputType, defaultValue: isPicker ? value : props.value || '', placeholder, disabled: Boolean(props.isDisabled), readOnly: isPicker})];
  if (isPicker) shellChildren.push(React.createElement('button', {key: 'b', type: 'button', tabIndex: -1}, '⌄'));
  return React.createElement('label', {className: `s2-field${isQuiet ? ' s2-field-quiet' : ''}${props.isDisabled ? ' is-disabled' : ''}`},
    React.createElement('span', null, labelFor(kind, props)),
    React.createElement('div', {className: 's2-field-shell'}, shellChildren)
  );
}

function slider(props) {
  return React.createElement('label', {className: 's2-slider'},
    React.createElement('span', null, labelFor('Slider', props), ' · 42'),
    React.createElement('input', {type: 'range', min: 0, max: 100, defaultValue: props.value ?? 42, disabled: Boolean(props.isDisabled)})
  );
}

function collection(kind, props) {
  const label = labelFor(kind, props);
  if (kind === 'Breadcrumbs') {
    return React.createElement('nav', {className: 's2-breadcrumbs'},
      React.createElement('a', {href: '#'}, 'Home'), React.createElement('span', null, '/'),
      React.createElement('a', {href: '#'}, 'Assets'), React.createElement('span', null, '/'),
      React.createElement('strong', null, 'Current')
    );
  }
  if (kind === 'Accordion') {
    return React.createElement('div', {className: 's2-accordion'},
      React.createElement('div', null, React.createElement('span', null, '▸'), label),
      React.createElement('p', null, 'Expanded Spectrum content.')
    );
  }
  if (kind === 'Tabs') {
    return React.createElement('section', {className: 's2-tabs'},
      React.createElement('div', {className: 's2-tabs-row'},
        React.createElement('button', {className: 'is-selected', type: 'button'}, 'Design'),
        React.createElement('button', {type: 'button'}, 'Code'),
        React.createElement('button', {type: 'button'}, 'Guidelines')),
      React.createElement('p', {className: 's2-text s2-text-muted', style: {margin: 0}}, 'Selected tab content')
    );
  }
  if (kind === 'Disclosure') {
    return React.createElement('span', {className: 's2-disclosure'}, label);
  }
  if (kind === 'Card') {
    return React.createElement('section', {className: `s2-card${props.isSelected ? ' is-selected' : ''}`},
      React.createElement('strong', {className: 's2-heading s2-heading-S'}, label),
      React.createElement('p', {className: 's2-text s2-text-muted', style: {margin: 0}}, 'Card body content.'));
  }
  return React.createElement('div', {className: 's2-surface'}, label);
}

function overlay(kind, props) {
  if (kind === 'Tooltip') {
    return React.createElement('span', {className: 's2-tooltip'}, props.content || labelFor(kind, props));
  }
  if (kind === 'Toast') {
    const variant = props.variant || 'informative';
    const mark = variant === 'positive' ? '✓' : variant === 'negative' ? '!' : 'i';
    return React.createElement('div', {className: `s2-toast s2-toast-${variant}`},
      React.createElement('i', null, mark),
      React.createElement('span', null, labelFor(kind, props)),
      React.createElement('button', {className: 's2-close', type: 'button'}, '×'));
  }
  if (kind === 'InlineAlert') {
    const variant = props.variant || 'informative';
    return React.createElement('div', {className: `s2-inline-alert s2-inline-alert-${variant}`},
      React.createElement('strong', null, props.heading || labelFor(kind, props)),
      React.createElement('span', null, 'Clear, concise supporting message.'));
  }
  if (kind === 'AlertDialog') {
    return React.createElement('section', {className: 's2-overlay'},
      React.createElement('strong', null, props.title || 'Delete this item?'),
      React.createElement('p', null, labelFor(kind, props) === kind.replace(/([a-z0-9])([A-Z])/g, '$1 $2') ? 'This action cannot be undone.' : labelFor(kind, props)),
      React.createElement('div', {className: 's2-inline-actions'},
        React.createElement('button', {className: 's2-button s2-button-outline', type: 'button'}, 'Cancel'),
        React.createElement('button', {className: 's2-button s2-button-fill-negative', type: 'button'}, 'Delete')));
  }
  return React.createElement('section', {className: 's2-overlay'},
    React.createElement('strong', null, labelFor(kind, props)),
    React.createElement('p', null, props.description || 'Clear, concise supporting message.'),
    React.createElement('div', {className: 's2-inline-actions'},
      React.createElement('button', {className: 's2-button s2-button-outline', type: 'button'}, 'Cancel'),
      React.createElement('button', {className: 's2-button s2-button-fill-accent', type: 'button'}, 'Confirm')));
}

export function renderSpectrumComponent(kind, props = {}) {
  const label = labelFor(kind, props);
  if (buttonKinds.has(kind)) return button(kind, props);
  if (kind === 'Link') return React.createElement('a', {className: 's2-link', href: '#', onClick: props.onPress}, label);
  if (kind === 'CloseButton') return React.createElement('button', {className: 's2-close', type: 'button', 'aria-label': props['aria-label'] || 'Close', disabled: Boolean(props.isDisabled)}, '×');
  if (kind === 'SegmentedControl') {
    return React.createElement('div', {className: 's2-segmented'},
      React.createElement('button', {className: 'is-selected', type: 'button'}, 'Day'),
      React.createElement('button', {type: 'button'}, 'Week'),
      React.createElement('button', {type: 'button'}, 'Month'));
  }
  if (choiceKinds.has(kind)) return choice(kind, props);
  if (groupKinds.has(kind)) {
    const inputType = kind === 'RadioGroup' ? 'radio' : 'checkbox';
    return React.createElement('fieldset', {className: 's2-choice-group'},
      React.createElement('legend', null, label),
      ['First option', 'Second option'].map((item, index) =>
        React.createElement('label', {className: `s2-choice${inputType === 'radio' ? ' s2-choice-radio' : ''}`, key: item},
          React.createElement('input', {type: inputType, name: kind, defaultChecked: index === 0}),
          React.createElement('span', null),
          React.createElement('b', {style: {fontWeight: 500}}, item))));
  }
  if (fieldKinds.has(kind)) return field(kind, props);
  if (kind === 'TextArea') {
    return React.createElement('label', {className: 's2-field'},
      React.createElement('span', null, label),
      React.createElement('textarea', {defaultValue: props.value || 'Write a clear description.', placeholder: props.placeholder, disabled: Boolean(props.isDisabled)}));
  }
  if (kind === 'Slider') return slider(props);
  if (kind === 'Text') return React.createElement('p', {className: `s2-text${props.isMuted ? ' s2-text-muted' : ''}`}, label);
  if (kind === 'Heading') return React.createElement('h3', {className: `s2-heading${sizeClass(props)}`}, label);
  if (kind === 'Content') return React.createElement('div', {className: 's2-content'}, label);
  if (kind === 'Divider') return React.createElement('hr', {className: props.orientation === 'vertical' ? 's2-divider-vertical' : 's2-divider'});
  if (kind === 'Badge') return React.createElement('span', {className: `s2-badge${props.variant && props.variant !== 'neutral' ? ` s2-badge-${props.variant}` : ''}`}, label);
  if (kind === 'StatusLight') return React.createElement('span', {className: `s2-status s2-status-${props.variant || 'informative'}`}, React.createElement('i', null), label);
  if (kind === 'LabeledValue') return React.createElement('dl', {className: 's2-labeled'}, React.createElement('dt', null, label), React.createElement('dd', null, props.value || 'Spectrum value'));
  if (kind === 'Avatar') return React.createElement('div', {className: `s2-avatar${sizeClass(props)}`, 'aria-label': props['aria-label'] || 'Avatar'}, props.children || 'RS');
  if (kind === 'IllustratedMessage') {
    return React.createElement('div', {className: 's2-illustrated'},
      React.createElement('div', {className: 's2-avatar s2-avatar-L'}, '!'),
      React.createElement('strong', null, props.heading || label),
      React.createElement('p', null, props.description || 'Supporting message text.'));
  }
  if (kind === 'ProgressBar' || kind === 'Meter') {
    return React.createElement('label', {className: 's2-progress'},
      React.createElement('span', null, label, ' · 64%'),
      React.createElement('div', {className: 's2-progress-track'}, React.createElement('div', {className: 's2-progress-fill'})));
  }
  if (kind === 'ProgressCircle') return React.createElement('div', {className: 's2-progress-circle', role: 'progressbar', 'aria-valuenow': props.value ?? 64, 'aria-valuemin': 0, 'aria-valuemax': 100});
  if (['Dialog', 'AlertDialog', 'Tooltip', 'Toast', 'InlineAlert'].includes(kind)) return overlay(kind, props);
  if (kind === 'Provider') {
    return React.createElement('section', {className: 's2-surface'},
      React.createElement('strong', {className: 's2-heading s2-heading-S'}, 'Provider'),
      React.createElement('p', {className: 's2-text s2-text-muted', style: {margin: '6px 0 0'}}, 'Theme, color scheme, scale, locale context root.'));
  }
  if (['Accordion', 'Breadcrumbs', 'Card', 'Disclosure', 'Tabs'].includes(kind)) return collection(kind, props);
  return React.createElement('div', {className: 's2-surface'}, label);
}

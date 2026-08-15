/* @ds-bundle: {"format":3,"namespace":"ReactSpectrum4_51380d","components":[{"name":"ActionButton","sourcePath":"components/actions/ActionButton.jsx"},{"name":"Button","sourcePath":"components/actions/Button.jsx"},{"name":"CloseButton","sourcePath":"components/actions/CloseButton.jsx"},{"name":"Link","sourcePath":"components/actions/Link.jsx"},{"name":"SegmentedControl","sourcePath":"components/actions/SegmentedControl.jsx"},{"name":"ToggleButton","sourcePath":"components/actions/ToggleButton.jsx"},{"name":"Accordion","sourcePath":"components/containers/Accordion.jsx"},{"name":"Breadcrumbs","sourcePath":"components/containers/Breadcrumbs.jsx"},{"name":"Card","sourcePath":"components/containers/Card.jsx"},{"name":"Disclosure","sourcePath":"components/containers/Disclosure.jsx"},{"name":"Provider","sourcePath":"components/containers/Provider.jsx"},{"name":"Tabs","sourcePath":"components/containers/Tabs.jsx"},{"name":"Avatar","sourcePath":"components/content/Avatar.jsx"},{"name":"Badge","sourcePath":"components/content/Badge.jsx"},{"name":"Content","sourcePath":"components/content/Content.jsx"},{"name":"Divider","sourcePath":"components/content/Divider.jsx"},{"name":"Heading","sourcePath":"components/content/Heading.jsx"},{"name":"IllustratedMessage","sourcePath":"components/content/IllustratedMessage.jsx"},{"name":"LabeledValue","sourcePath":"components/content/LabeledValue.jsx"},{"name":"StatusLight","sourcePath":"components/content/StatusLight.jsx"},{"name":"Text","sourcePath":"components/content/Text.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Checkbox.jsx"},{"name":"CheckboxGroup","sourcePath":"components/forms/CheckboxGroup.jsx"},{"name":"ComboBox","sourcePath":"components/forms/ComboBox.jsx"},{"name":"NumberField","sourcePath":"components/forms/NumberField.jsx"},{"name":"Picker","sourcePath":"components/forms/Picker.jsx"},{"name":"RadioGroup","sourcePath":"components/forms/RadioGroup.jsx"},{"name":"SearchField","sourcePath":"components/forms/SearchField.jsx"},{"name":"Slider","sourcePath":"components/forms/Slider.jsx"},{"name":"Switch","sourcePath":"components/forms/Switch.jsx"},{"name":"TextArea","sourcePath":"components/forms/TextArea.jsx"},{"name":"TextField","sourcePath":"components/forms/TextField.jsx"},{"name":"AlertDialog","sourcePath":"components/overlays/AlertDialog.jsx"},{"name":"Dialog","sourcePath":"components/overlays/Dialog.jsx"},{"name":"InlineAlert","sourcePath":"components/overlays/InlineAlert.jsx"},{"name":"ProgressBar","sourcePath":"components/overlays/ProgressBar.jsx"},{"name":"ProgressCircle","sourcePath":"components/overlays/ProgressCircle.jsx"},{"name":"Toast","sourcePath":"components/overlays/Toast.jsx"},{"name":"Tooltip","sourcePath":"components/overlays/Tooltip.jsx"}],"sourceHashes":{"components/actions/ActionButton.jsx":"5386d6732fa0","components/actions/Button.jsx":"18bc4055ae37","components/actions/CloseButton.jsx":"3959b8a709ab","components/actions/Link.jsx":"2ee73203c41a","components/actions/SegmentedControl.jsx":"e96ebb1d470b","components/actions/ToggleButton.jsx":"0c1ac5a4e2a2","components/containers/Accordion.jsx":"b609e89e4f51","components/containers/Breadcrumbs.jsx":"5865449a252e","components/containers/Card.jsx":"44f2d86fb78b","components/containers/Disclosure.jsx":"4ee032cffbf0","components/containers/Provider.jsx":"73192b33cf5b","components/containers/Tabs.jsx":"29b237fcd235","components/content/Avatar.jsx":"14f22066df56","components/content/Badge.jsx":"cf3c6947ea1e","components/content/Content.jsx":"5443cd9948a7","components/content/Divider.jsx":"95f2e8331ea0","components/content/Heading.jsx":"50bbb6342680","components/content/IllustratedMessage.jsx":"9ebcc43f6453","components/content/LabeledValue.jsx":"c123b4f0a4ce","components/content/StatusLight.jsx":"825374ee2baf","components/content/Text.jsx":"77141c798d7e","components/forms/Checkbox.jsx":"f5c03879ffd7","components/forms/CheckboxGroup.jsx":"71123c2c1552","components/forms/ComboBox.jsx":"344c5308d0ca","components/forms/NumberField.jsx":"cc00ba06e5b3","components/forms/Picker.jsx":"85c53128e323","components/forms/RadioGroup.jsx":"46696a564f20","components/forms/SearchField.jsx":"a0b9ec0db780","components/forms/Slider.jsx":"d6275df306fe","components/forms/Switch.jsx":"ea88de09bab2","components/forms/TextArea.jsx":"d5bff97a7852","components/forms/TextField.jsx":"5cfef2f024d9","components/overlays/AlertDialog.jsx":"aaf9b8f83994","components/overlays/Dialog.jsx":"94e27487f999","components/overlays/InlineAlert.jsx":"b902165cd451","components/overlays/ProgressBar.jsx":"005e14271e3d","components/overlays/ProgressCircle.jsx":"eefffb4fb3db","components/overlays/Toast.jsx":"f579535199cf","components/overlays/Tooltip.jsx":"e493966cd6a7","components/shared/spectrumPrimitive.jsx":"02b7e0e93906"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.ReactSpectrum4_51380d = window.ReactSpectrum4_51380d || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/shared/spectrumPrimitive.jsx
try { (() => {
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
  if (isQuiet || kind === 'ActionButton' && !props.isSelected) styleClass = 's2-button-quiet';else if (fillStyle === 'outline' || variant === 'secondary') styleClass = 's2-button-outline';else if (variant === 'negative') styleClass = 's2-button-fill-negative';else if (variant === 'primary' || variant === 'accent') styleClass = 's2-button-fill-accent';else styleClass = 's2-button-fill-neutral';
  const classes = ['s2-button', styleClass];
  if (kind === 'ActionButton') classes.push('s2-button-icon');
  if (props.isSelected) classes.push('is-selected');
  if (props.isDisabled) classes.push('is-disabled');
  if (props.size) classes.push(`s2-button-size-${props.size}`);
  const glyph = kind === 'ActionButton' ? props.isSelected ? '✓' : '＋' : kind === 'ToggleButton' ? props.isSelected ? '★' : '☆' : '';
  return React.createElement('button', {
    className: classes.join(' '),
    type: 'button',
    disabled: Boolean(props.isDisabled),
    onClick: props.onPress
  }, glyph, labelFor(kind, props));
}
function choice(kind, props) {
  const inputType = kind === 'Switch' || kind === 'Checkbox' ? 'checkbox' : 'radio';
  const isSwitch = kind === 'Switch';
  return React.createElement('label', {
    className: `s2-choice${isSwitch ? ' s2-choice-switch' : kind === 'Radio' ? ' s2-choice-radio' : ''}`
  }, React.createElement('input', {
    type: inputType,
    defaultChecked: props.isSelected !== false,
    disabled: Boolean(props.isDisabled)
  }), React.createElement('span', null), React.createElement('b', {
    style: {
      fontWeight: 500
    }
  }, labelFor(kind, props)));
}
function field(kind, props) {
  const inputType = kind === 'SearchField' ? 'search' : kind === 'NumberField' ? 'number' : 'text';
  const placeholder = props.placeholder || (kind === 'SearchField' ? 'Search' : '');
  const value = props.value ?? (kind === 'NumberField' ? '42' : kind === 'Picker' ? 'Select option' : kind === 'ComboBox' ? 'Spectrum value' : 'Spectrum value');
  const isPicker = kind === 'Picker' || kind === 'ComboBox';
  const isQuiet = props.isQuiet;
  const shellChildren = [React.createElement('input', {
    key: 'i',
    type: inputType,
    defaultValue: isPicker ? value : props.value || '',
    placeholder,
    disabled: Boolean(props.isDisabled),
    readOnly: isPicker
  })];
  if (isPicker) shellChildren.push(React.createElement('button', {
    key: 'b',
    type: 'button',
    tabIndex: -1
  }, '⌄'));
  return React.createElement('label', {
    className: `s2-field${isQuiet ? ' s2-field-quiet' : ''}${props.isDisabled ? ' is-disabled' : ''}`
  }, React.createElement('span', null, labelFor(kind, props)), React.createElement('div', {
    className: 's2-field-shell'
  }, shellChildren));
}
function slider(props) {
  return React.createElement('label', {
    className: 's2-slider'
  }, React.createElement('span', null, labelFor('Slider', props), ' · 42'), React.createElement('input', {
    type: 'range',
    min: 0,
    max: 100,
    defaultValue: props.value ?? 42,
    disabled: Boolean(props.isDisabled)
  }));
}
function collection(kind, props) {
  const label = labelFor(kind, props);
  if (kind === 'Breadcrumbs') {
    return React.createElement('nav', {
      className: 's2-breadcrumbs'
    }, React.createElement('a', {
      href: '#'
    }, 'Home'), React.createElement('span', null, '/'), React.createElement('a', {
      href: '#'
    }, 'Assets'), React.createElement('span', null, '/'), React.createElement('strong', null, 'Current'));
  }
  if (kind === 'Accordion') {
    return React.createElement('div', {
      className: 's2-accordion'
    }, React.createElement('div', null, React.createElement('span', null, '▸'), label), React.createElement('p', null, 'Expanded Spectrum content.'));
  }
  if (kind === 'Tabs') {
    return React.createElement('section', {
      className: 's2-tabs'
    }, React.createElement('div', {
      className: 's2-tabs-row'
    }, React.createElement('button', {
      className: 'is-selected',
      type: 'button'
    }, 'Design'), React.createElement('button', {
      type: 'button'
    }, 'Code'), React.createElement('button', {
      type: 'button'
    }, 'Guidelines')), React.createElement('p', {
      className: 's2-text s2-text-muted',
      style: {
        margin: 0
      }
    }, 'Selected tab content'));
  }
  if (kind === 'Disclosure') {
    return React.createElement('span', {
      className: 's2-disclosure'
    }, label);
  }
  if (kind === 'Card') {
    return React.createElement('section', {
      className: `s2-card${props.isSelected ? ' is-selected' : ''}`
    }, React.createElement('strong', {
      className: 's2-heading s2-heading-S'
    }, label), React.createElement('p', {
      className: 's2-text s2-text-muted',
      style: {
        margin: 0
      }
    }, 'Card body content.'));
  }
  return React.createElement('div', {
    className: 's2-surface'
  }, label);
}
function overlay(kind, props) {
  if (kind === 'Tooltip') {
    return React.createElement('span', {
      className: 's2-tooltip'
    }, props.content || labelFor(kind, props));
  }
  if (kind === 'Toast') {
    const variant = props.variant || 'informative';
    const mark = variant === 'positive' ? '✓' : variant === 'negative' ? '!' : 'i';
    return React.createElement('div', {
      className: `s2-toast s2-toast-${variant}`
    }, React.createElement('i', null, mark), React.createElement('span', null, labelFor(kind, props)), React.createElement('button', {
      className: 's2-close',
      type: 'button'
    }, '×'));
  }
  if (kind === 'InlineAlert') {
    const variant = props.variant || 'informative';
    return React.createElement('div', {
      className: `s2-inline-alert s2-inline-alert-${variant}`
    }, React.createElement('strong', null, props.heading || labelFor(kind, props)), React.createElement('span', null, 'Clear, concise supporting message.'));
  }
  if (kind === 'AlertDialog') {
    return React.createElement('section', {
      className: 's2-overlay'
    }, React.createElement('strong', null, props.title || 'Delete this item?'), React.createElement('p', null, labelFor(kind, props) === kind.replace(/([a-z0-9])([A-Z])/g, '$1 $2') ? 'This action cannot be undone.' : labelFor(kind, props)), React.createElement('div', {
      className: 's2-inline-actions'
    }, React.createElement('button', {
      className: 's2-button s2-button-outline',
      type: 'button'
    }, 'Cancel'), React.createElement('button', {
      className: 's2-button s2-button-fill-negative',
      type: 'button'
    }, 'Delete')));
  }
  return React.createElement('section', {
    className: 's2-overlay'
  }, React.createElement('strong', null, labelFor(kind, props)), React.createElement('p', null, props.description || 'Clear, concise supporting message.'), React.createElement('div', {
    className: 's2-inline-actions'
  }, React.createElement('button', {
    className: 's2-button s2-button-outline',
    type: 'button'
  }, 'Cancel'), React.createElement('button', {
    className: 's2-button s2-button-fill-accent',
    type: 'button'
  }, 'Confirm')));
}
function renderSpectrumComponent(kind, props = {}) {
  const label = labelFor(kind, props);
  if (buttonKinds.has(kind)) return button(kind, props);
  if (kind === 'Link') return React.createElement('a', {
    className: 's2-link',
    href: '#',
    onClick: props.onPress
  }, label);
  if (kind === 'CloseButton') return React.createElement('button', {
    className: 's2-close',
    type: 'button',
    'aria-label': props['aria-label'] || 'Close',
    disabled: Boolean(props.isDisabled)
  }, '×');
  if (kind === 'SegmentedControl') {
    return React.createElement('div', {
      className: 's2-segmented'
    }, React.createElement('button', {
      className: 'is-selected',
      type: 'button'
    }, 'Day'), React.createElement('button', {
      type: 'button'
    }, 'Week'), React.createElement('button', {
      type: 'button'
    }, 'Month'));
  }
  if (choiceKinds.has(kind)) return choice(kind, props);
  if (groupKinds.has(kind)) {
    const inputType = kind === 'RadioGroup' ? 'radio' : 'checkbox';
    return React.createElement('fieldset', {
      className: 's2-choice-group'
    }, React.createElement('legend', null, label), ['First option', 'Second option'].map((item, index) => React.createElement('label', {
      className: `s2-choice${inputType === 'radio' ? ' s2-choice-radio' : ''}`,
      key: item
    }, React.createElement('input', {
      type: inputType,
      name: kind,
      defaultChecked: index === 0
    }), React.createElement('span', null), React.createElement('b', {
      style: {
        fontWeight: 500
      }
    }, item))));
  }
  if (fieldKinds.has(kind)) return field(kind, props);
  if (kind === 'TextArea') {
    return React.createElement('label', {
      className: 's2-field'
    }, React.createElement('span', null, label), React.createElement('textarea', {
      defaultValue: props.value || 'Write a clear description.',
      placeholder: props.placeholder,
      disabled: Boolean(props.isDisabled)
    }));
  }
  if (kind === 'Slider') return slider(props);
  if (kind === 'Text') return React.createElement('p', {
    className: `s2-text${props.isMuted ? ' s2-text-muted' : ''}`
  }, label);
  if (kind === 'Heading') return React.createElement('h3', {
    className: `s2-heading${sizeClass(props)}`
  }, label);
  if (kind === 'Content') return React.createElement('div', {
    className: 's2-content'
  }, label);
  if (kind === 'Divider') return React.createElement('hr', {
    className: props.orientation === 'vertical' ? 's2-divider-vertical' : 's2-divider'
  });
  if (kind === 'Badge') return React.createElement('span', {
    className: `s2-badge${props.variant && props.variant !== 'neutral' ? ` s2-badge-${props.variant}` : ''}`
  }, label);
  if (kind === 'StatusLight') return React.createElement('span', {
    className: `s2-status s2-status-${props.variant || 'informative'}`
  }, React.createElement('i', null), label);
  if (kind === 'LabeledValue') return React.createElement('dl', {
    className: 's2-labeled'
  }, React.createElement('dt', null, label), React.createElement('dd', null, props.value || 'Spectrum value'));
  if (kind === 'Avatar') return React.createElement('div', {
    className: `s2-avatar${sizeClass(props)}`,
    'aria-label': props['aria-label'] || 'Avatar'
  }, props.children || 'RS');
  if (kind === 'IllustratedMessage') {
    return React.createElement('div', {
      className: 's2-illustrated'
    }, React.createElement('div', {
      className: 's2-avatar s2-avatar-L'
    }, '!'), React.createElement('strong', null, props.heading || label), React.createElement('p', null, props.description || 'Supporting message text.'));
  }
  if (kind === 'ProgressBar' || kind === 'Meter') {
    return React.createElement('label', {
      className: 's2-progress'
    }, React.createElement('span', null, label, ' · 64%'), React.createElement('div', {
      className: 's2-progress-track'
    }, React.createElement('div', {
      className: 's2-progress-fill'
    })));
  }
  if (kind === 'ProgressCircle') return React.createElement('div', {
    className: 's2-progress-circle',
    role: 'progressbar',
    'aria-valuenow': props.value ?? 64,
    'aria-valuemin': 0,
    'aria-valuemax': 100
  });
  if (['Dialog', 'AlertDialog', 'Tooltip', 'Toast', 'InlineAlert'].includes(kind)) return overlay(kind, props);
  if (kind === 'Provider') {
    return React.createElement('section', {
      className: 's2-surface'
    }, React.createElement('strong', {
      className: 's2-heading s2-heading-S'
    }, 'Provider'), React.createElement('p', {
      className: 's2-text s2-text-muted',
      style: {
        margin: '6px 0 0'
      }
    }, 'Theme, color scheme, scale, locale context root.'));
  }
  if (['Accordion', 'Breadcrumbs', 'Card', 'Disclosure', 'Tabs'].includes(kind)) return collection(kind, props);
  return React.createElement('div', {
    className: 's2-surface'
  }, label);
}
Object.assign(__ds_scope, { renderSpectrumComponent });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/shared/spectrumPrimitive.jsx", error: String((e && e.message) || e) }); }

// components/actions/ActionButton.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function ActionButton(props) {
  return renderSpectrumComponent('ActionButton', props);
}
Object.assign(__ds_scope, { ActionButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/actions/ActionButton.jsx", error: String((e && e.message) || e) }); }

// components/actions/Button.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Button(props) {
  return renderSpectrumComponent('Button', props);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/actions/Button.jsx", error: String((e && e.message) || e) }); }

// components/actions/CloseButton.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function CloseButton(props) {
  return renderSpectrumComponent('CloseButton', props);
}
Object.assign(__ds_scope, { CloseButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/actions/CloseButton.jsx", error: String((e && e.message) || e) }); }

// components/actions/Link.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Link(props) {
  return renderSpectrumComponent('Link', props);
}
Object.assign(__ds_scope, { Link });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/actions/Link.jsx", error: String((e && e.message) || e) }); }

// components/actions/SegmentedControl.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function SegmentedControl(props) {
  return renderSpectrumComponent('SegmentedControl', props);
}
Object.assign(__ds_scope, { SegmentedControl });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/actions/SegmentedControl.jsx", error: String((e && e.message) || e) }); }

// components/actions/ToggleButton.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function ToggleButton(props) {
  return renderSpectrumComponent('ToggleButton', props);
}
Object.assign(__ds_scope, { ToggleButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/actions/ToggleButton.jsx", error: String((e && e.message) || e) }); }

// components/containers/Accordion.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Accordion(props) {
  return renderSpectrumComponent('Accordion', props);
}
Object.assign(__ds_scope, { Accordion });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/containers/Accordion.jsx", error: String((e && e.message) || e) }); }

// components/containers/Breadcrumbs.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Breadcrumbs(props) {
  return renderSpectrumComponent('Breadcrumbs', props);
}
Object.assign(__ds_scope, { Breadcrumbs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/containers/Breadcrumbs.jsx", error: String((e && e.message) || e) }); }

// components/containers/Card.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Card(props) {
  return renderSpectrumComponent('Card', props);
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/containers/Card.jsx", error: String((e && e.message) || e) }); }

// components/containers/Disclosure.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Disclosure(props) {
  return renderSpectrumComponent('Disclosure', props);
}
Object.assign(__ds_scope, { Disclosure });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/containers/Disclosure.jsx", error: String((e && e.message) || e) }); }

// components/containers/Provider.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Provider(props) {
  return renderSpectrumComponent('Provider', props);
}
Object.assign(__ds_scope, { Provider });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/containers/Provider.jsx", error: String((e && e.message) || e) }); }

// components/containers/Tabs.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Tabs(props) {
  return renderSpectrumComponent('Tabs', props);
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/containers/Tabs.jsx", error: String((e && e.message) || e) }); }

// components/content/Avatar.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Avatar(props) {
  return renderSpectrumComponent('Avatar', props);
}
Object.assign(__ds_scope, { Avatar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/Avatar.jsx", error: String((e && e.message) || e) }); }

// components/content/Badge.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Badge(props) {
  return renderSpectrumComponent('Badge', props);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/Badge.jsx", error: String((e && e.message) || e) }); }

// components/content/Content.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Content(props) {
  return renderSpectrumComponent('Content', props);
}
Object.assign(__ds_scope, { Content });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/Content.jsx", error: String((e && e.message) || e) }); }

// components/content/Divider.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Divider(props) {
  return renderSpectrumComponent('Divider', props);
}
Object.assign(__ds_scope, { Divider });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/Divider.jsx", error: String((e && e.message) || e) }); }

// components/content/Heading.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Heading(props) {
  return renderSpectrumComponent('Heading', props);
}
Object.assign(__ds_scope, { Heading });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/Heading.jsx", error: String((e && e.message) || e) }); }

// components/content/IllustratedMessage.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function IllustratedMessage(props) {
  return renderSpectrumComponent('IllustratedMessage', props);
}
Object.assign(__ds_scope, { IllustratedMessage });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/IllustratedMessage.jsx", error: String((e && e.message) || e) }); }

// components/content/LabeledValue.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function LabeledValue(props) {
  return renderSpectrumComponent('LabeledValue', props);
}
Object.assign(__ds_scope, { LabeledValue });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/LabeledValue.jsx", error: String((e && e.message) || e) }); }

// components/content/StatusLight.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function StatusLight(props) {
  return renderSpectrumComponent('StatusLight', props);
}
Object.assign(__ds_scope, { StatusLight });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/StatusLight.jsx", error: String((e && e.message) || e) }); }

// components/content/Text.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Text(props) {
  return renderSpectrumComponent('Text', props);
}
Object.assign(__ds_scope, { Text });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/Text.jsx", error: String((e && e.message) || e) }); }

// components/forms/Checkbox.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Checkbox(props) {
  return renderSpectrumComponent('Checkbox', props);
}
Object.assign(__ds_scope, { Checkbox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Checkbox.jsx", error: String((e && e.message) || e) }); }

// components/forms/CheckboxGroup.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function CheckboxGroup(props) {
  return renderSpectrumComponent('CheckboxGroup', props);
}
Object.assign(__ds_scope, { CheckboxGroup });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/CheckboxGroup.jsx", error: String((e && e.message) || e) }); }

// components/forms/ComboBox.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function ComboBox(props) {
  return renderSpectrumComponent('ComboBox', props);
}
Object.assign(__ds_scope, { ComboBox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/ComboBox.jsx", error: String((e && e.message) || e) }); }

// components/forms/NumberField.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function NumberField(props) {
  return renderSpectrumComponent('NumberField', props);
}
Object.assign(__ds_scope, { NumberField });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/NumberField.jsx", error: String((e && e.message) || e) }); }

// components/forms/Picker.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Picker(props) {
  return renderSpectrumComponent('Picker', props);
}
Object.assign(__ds_scope, { Picker });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Picker.jsx", error: String((e && e.message) || e) }); }

// components/forms/RadioGroup.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function RadioGroup(props) {
  return renderSpectrumComponent('RadioGroup', props);
}
Object.assign(__ds_scope, { RadioGroup });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/RadioGroup.jsx", error: String((e && e.message) || e) }); }

// components/forms/SearchField.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function SearchField(props) {
  return renderSpectrumComponent('SearchField', props);
}
Object.assign(__ds_scope, { SearchField });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/SearchField.jsx", error: String((e && e.message) || e) }); }

// components/forms/Slider.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Slider(props) {
  return renderSpectrumComponent('Slider', props);
}
Object.assign(__ds_scope, { Slider });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Slider.jsx", error: String((e && e.message) || e) }); }

// components/forms/Switch.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Switch(props) {
  return renderSpectrumComponent('Switch', props);
}
Object.assign(__ds_scope, { Switch });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Switch.jsx", error: String((e && e.message) || e) }); }

// components/forms/TextArea.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function TextArea(props) {
  return renderSpectrumComponent('TextArea', props);
}
Object.assign(__ds_scope, { TextArea });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/TextArea.jsx", error: String((e && e.message) || e) }); }

// components/forms/TextField.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function TextField(props) {
  return renderSpectrumComponent('TextField', props);
}
Object.assign(__ds_scope, { TextField });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/TextField.jsx", error: String((e && e.message) || e) }); }

// components/overlays/AlertDialog.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function AlertDialog(props) {
  return renderSpectrumComponent('AlertDialog', props);
}
Object.assign(__ds_scope, { AlertDialog });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/overlays/AlertDialog.jsx", error: String((e && e.message) || e) }); }

// components/overlays/Dialog.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Dialog(props) {
  return renderSpectrumComponent('Dialog', props);
}
Object.assign(__ds_scope, { Dialog });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/overlays/Dialog.jsx", error: String((e && e.message) || e) }); }

// components/overlays/InlineAlert.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function InlineAlert(props) {
  return renderSpectrumComponent('InlineAlert', props);
}
Object.assign(__ds_scope, { InlineAlert });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/overlays/InlineAlert.jsx", error: String((e && e.message) || e) }); }

// components/overlays/ProgressBar.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function ProgressBar(props) {
  return renderSpectrumComponent('ProgressBar', props);
}
Object.assign(__ds_scope, { ProgressBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/overlays/ProgressBar.jsx", error: String((e && e.message) || e) }); }

// components/overlays/ProgressCircle.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function ProgressCircle(props) {
  return renderSpectrumComponent('ProgressCircle', props);
}
Object.assign(__ds_scope, { ProgressCircle });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/overlays/ProgressCircle.jsx", error: String((e && e.message) || e) }); }

// components/overlays/Toast.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Toast(props) {
  return renderSpectrumComponent('Toast', props);
}
Object.assign(__ds_scope, { Toast });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/overlays/Toast.jsx", error: String((e && e.message) || e) }); }

// components/overlays/Tooltip.jsx
try { (() => {
const {
  renderSpectrumComponent
} = __ds_scope;
function Tooltip(props) {
  return renderSpectrumComponent('Tooltip', props);
}
Object.assign(__ds_scope, { Tooltip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/overlays/Tooltip.jsx", error: String((e && e.message) || e) }); }

__ds_ns.ActionButton = __ds_scope.ActionButton;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.CloseButton = __ds_scope.CloseButton;

__ds_ns.Link = __ds_scope.Link;

__ds_ns.SegmentedControl = __ds_scope.SegmentedControl;

__ds_ns.ToggleButton = __ds_scope.ToggleButton;

__ds_ns.Accordion = __ds_scope.Accordion;

__ds_ns.Breadcrumbs = __ds_scope.Breadcrumbs;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.Disclosure = __ds_scope.Disclosure;

__ds_ns.Provider = __ds_scope.Provider;

__ds_ns.Tabs = __ds_scope.Tabs;

__ds_ns.Avatar = __ds_scope.Avatar;

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Content = __ds_scope.Content;

__ds_ns.Divider = __ds_scope.Divider;

__ds_ns.Heading = __ds_scope.Heading;

__ds_ns.IllustratedMessage = __ds_scope.IllustratedMessage;

__ds_ns.LabeledValue = __ds_scope.LabeledValue;

__ds_ns.StatusLight = __ds_scope.StatusLight;

__ds_ns.Text = __ds_scope.Text;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.CheckboxGroup = __ds_scope.CheckboxGroup;

__ds_ns.ComboBox = __ds_scope.ComboBox;

__ds_ns.NumberField = __ds_scope.NumberField;

__ds_ns.Picker = __ds_scope.Picker;

__ds_ns.RadioGroup = __ds_scope.RadioGroup;

__ds_ns.SearchField = __ds_scope.SearchField;

__ds_ns.Slider = __ds_scope.Slider;

__ds_ns.Switch = __ds_scope.Switch;

__ds_ns.TextArea = __ds_scope.TextArea;

__ds_ns.TextField = __ds_scope.TextField;

__ds_ns.AlertDialog = __ds_scope.AlertDialog;

__ds_ns.Dialog = __ds_scope.Dialog;

__ds_ns.InlineAlert = __ds_scope.InlineAlert;

__ds_ns.ProgressBar = __ds_scope.ProgressBar;

__ds_ns.ProgressCircle = __ds_scope.ProgressCircle;

__ds_ns.Toast = __ds_scope.Toast;

__ds_ns.Tooltip = __ds_scope.Tooltip;

})();

import type {ReactElement, ReactNode} from 'react';

export interface AccordionProps {
  children?: ReactNode;
  onExpandedChange?: (keys: Set<string>) => void;
}

export declare function Accordion(props: AccordionProps): ReactElement;

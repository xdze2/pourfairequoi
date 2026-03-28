/** Graph node: a goal or task */
export type Node = {
  id: string;
  description: string;
  context: string;
  type: string;
  status: string;
  creation_date: string;
  last_modification_date: string;
};

/** Directed edge; semantic type is a free-form label (why, how, but, …) */
export type Link = {
  id: string;
  src_id: string;
  tgt_id: string;
  type: string;
  creation_date: string;
};

export type PfqSnapshot = {
  version: 1;
  nodes: Node[];
  links: Link[];
};

export const LINK_TYPES_SUGGESTED = ['why', 'how', 'but', 'alternative_to', 'constrain', 'require'] as const;

/**
 * Pending Document entity - documents awaiting user acceptance.
 */

export class PendingDocument {
  constructor(
    public readonly id: string,
    public readonly documentType: string,
    public readonly version: string,
    public readonly title: string
  ) {}

  static fromApi(data: {
    id: string;
    document_type: string;
    version: string;
    title: string;
  }): PendingDocument {
    return new PendingDocument(
      data.id,
      data.document_type,
      data.version,
      data.title
    );
  }
}

/**
 * User domain entity.
 * Pure business logic, no external dependencies.
 */

export class User {
  constructor(
    public readonly id: string,
    public readonly walletAddress: string,
    public readonly createdAt: Date,
    public readonly updatedAt: Date
  ) {}

  static fromApi(data: {
    id: string;
    wallet_address: string;
    created_at: string;
    updated_at: string;
  }): User {
    return new User(
      data.id,
      data.wallet_address,
      new Date(data.created_at),
      new Date(data.updated_at)
    );
  }

  get shortAddress(): string {
    return `${this.walletAddress.slice(0, 4)}...${this.walletAddress.slice(-4)}`;
  }

  isEqual(other: User): boolean {
    return this.id === other.id;
  }
}

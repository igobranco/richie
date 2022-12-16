/**
 * An error to raise when a request failed with a message that can be presented to the user.
 * It has been designed to store response.status, response.statusText and a message.
 */
import { HttpError } from './HttpError';

export class LocalizedHttpError extends HttpError {
  message: string;
    
  constructor(status: number, statusText: string, message: string) {
    super(status, statusText);
    this.message = message;
  }
}

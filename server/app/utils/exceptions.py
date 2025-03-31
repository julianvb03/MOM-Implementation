"""
This module contains a function to raise an 
HTTPException and log the error
when an exception occurs in the application.
It is used to handle exceptions in a consistent
way across the application.
The function takes an exception and a logger 
instance as arguments,
logs the error message, and raises an HTTPException
with a 500 status code.
The logger instance is used to log the error message.
"""
from logging import Logger
from fastapi import HTTPException, status


def raise_exception(e: Exception, logger: Logger):
    """
    Raise an HTTPException and log the error

    Arguments:
        e (Exception) : The exception that was raised
        logger (Logger) : The logger instance to log

    Raises:
        HTTPException : The HTTPException with the error message
    """
    logger.error(f"Error : {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    )

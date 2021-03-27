from irctk import numerics


def test_rfc1459_error_numerics() -> None:
    assert numerics.ERR_NOSUCHNICK == 401
    assert numerics.ERR_NOSUCHSERVER == 402
    assert numerics.ERR_NOSUCHCHANNEL == 403
    assert numerics.ERR_CANNOTSENDTOCHAN == 404
    assert numerics.ERR_TOOMANYCHANNELS == 405
    assert numerics.ERR_WASNOSUCHNICK == 406
    assert numerics.ERR_TOOMANYTARGETS == 407
    assert numerics.ERR_NOORIGIN == 409
    assert numerics.ERR_NORECIPIENT == 411
    assert numerics.ERR_NOTEXTTOSEND == 412
    assert numerics.ERR_NOTOPLEVEL == 413
    assert numerics.ERR_WILDTOPLEVEL == 414
    assert numerics.ERR_UNKNOWNCOMMAND == 421
    assert numerics.ERR_NOMOTD == 422
    assert numerics.ERR_NOADMININFO == 423
    assert numerics.ERR_FILEERROR == 424
    assert numerics.ERR_NONICKNAMEGIVEN == 431
    assert numerics.ERR_ERRONEUSNICKNAME == 432
    assert numerics.ERR_NICKNAMEINUSE == 433
    assert numerics.ERR_NICKCOLLISION == 436
    assert numerics.ERR_USERNOTINCHANNEL == 441
    assert numerics.ERR_NOTONCHANNEL == 442
    assert numerics.ERR_USERONCHANNEL == 443
    assert numerics.ERR_NOLOGIN == 444
    assert numerics.ERR_SUMMONDISABLED == 445
    assert numerics.ERR_USERSDISABLED == 446
    assert numerics.ERR_NOTREGISTERED == 451
    assert numerics.ERR_NEEDMOREPARAMS == 461
    assert numerics.ERR_ALREADYREGISTRED == 462
    assert numerics.ERR_NOPERMFORHOST == 463
    assert numerics.ERR_PASSWDMISMATCH == 464
    assert numerics.ERR_YOUREBANNEDCREEP == 465
    assert numerics.ERR_KEYSET == 467
    assert numerics.ERR_CHANNELISFULL == 471
    assert numerics.ERR_UNKNOWNMODE == 472
    assert numerics.ERR_INVITEONLYCHAN == 473
    assert numerics.ERR_BANNEDFROMCHAN == 474
    assert numerics.ERR_BADCHANNELKEY == 475
    assert numerics.ERR_NOPRIVILEGES == 481
    assert numerics.ERR_CHANOPRIVSNEEDED == 482
    assert numerics.ERR_CANTKILLSERVER == 483
    assert numerics.ERR_NOOPERHOST == 491
    assert numerics.ERR_UMODEUNKNOWNFLAG == 501
    assert numerics.ERR_USERSDONTMATCH == 502


def test_rfc1459_command_numerics() -> None:
    assert numerics.RPL_NONE == 300
    assert numerics.RPL_USERHOST == 302
    assert numerics.RPL_ISON == 303
    assert numerics.RPL_AWAY == 301
    assert numerics.RPL_UNAWAY == 305
    assert numerics.RPL_NOWAWAY == 306
    assert numerics.RPL_WHOISUSER == 311
    assert numerics.RPL_WHOISSERVER == 312
    assert numerics.RPL_WHOISOPERATOR == 313
    assert numerics.RPL_WHOISIDLE == 317
    assert numerics.RPL_ENDOFWHOIS == 318
    assert numerics.RPL_WHOISCHANNELS == 319
    assert numerics.RPL_WHOWASUSER == 314
    assert numerics.RPL_ENDOFWHOWAS == 369
    assert numerics.RPL_LISTSTART == 321
    assert numerics.RPL_LIST == 322
    assert numerics.RPL_LISTEND == 323
    assert numerics.RPL_CHANNELMODEIS == 324
    assert numerics.RPL_NOTOPIC == 331
    assert numerics.RPL_TOPIC == 332
    assert numerics.RPL_INVITING == 341
    assert numerics.RPL_SUMMONING == 342
    assert numerics.RPL_VERSION == 351
    assert numerics.RPL_WHOREPLY == 352
    assert numerics.RPL_ENDOFWHO == 315
    assert numerics.RPL_NAMREPLY == 353
    assert numerics.RPL_ENDOFNAMES == 366
    assert numerics.RPL_LINKS == 364
    assert numerics.RPL_ENDOFLINKS == 365
    assert numerics.RPL_BANLIST == 367
    assert numerics.RPL_ENDOFBANLIST == 368
    assert numerics.RPL_INFO == 371
    assert numerics.RPL_ENDOFINFO == 374
    assert numerics.RPL_MOTDSTART == 375
    assert numerics.RPL_MOTD == 372
    assert numerics.RPL_ENDOFMOTD == 376
    assert numerics.RPL_YOUREOPER == 381
    assert numerics.RPL_REHASHING == 382
    assert numerics.RPL_TIME == 391
    assert numerics.RPL_USERSSTART == 392
    assert numerics.RPL_USERS == 393
    assert numerics.RPL_ENDOFUSERS == 394
    assert numerics.RPL_NOUSERS == 395
    assert numerics.RPL_TRACELINK == 200
    assert numerics.RPL_TRACECONNECTING == 201
    assert numerics.RPL_TRACEHANDSHAKE == 202
    assert numerics.RPL_TRACEUNKNOWN == 203
    assert numerics.RPL_TRACEOPERATOR == 204
    assert numerics.RPL_TRACEUSER == 205
    assert numerics.RPL_TRACESERVER == 206
    assert numerics.RPL_TRACENEWTYPE == 208
    assert numerics.RPL_TRACELOG == 261
    assert numerics.RPL_STATSLINKINFO == 211
    assert numerics.RPL_STATSCOMMANDS == 212
    assert numerics.RPL_STATSCLINE == 213
    assert numerics.RPL_STATSNLINE == 214
    assert numerics.RPL_STATSILINE == 215
    assert numerics.RPL_STATSKLINE == 216
    assert numerics.RPL_STATSYLINE == 218
    assert numerics.RPL_ENDOFSTATS == 219
    assert numerics.RPL_STATSLLINE == 241
    assert numerics.RPL_STATSUPTIME == 242
    assert numerics.RPL_STATSOLINE == 243
    assert numerics.RPL_STATSHLINE == 244
    assert numerics.RPL_UMODEIS == 221
    assert numerics.RPL_LUSERCLIENT == 251
    assert numerics.RPL_LUSEROP == 252
    assert numerics.RPL_LUSERUNKNOWN == 253
    assert numerics.RPL_LUSERCHANNELS == 254
    assert numerics.RPL_LUSERME == 255
    assert numerics.RPL_ADMINME == 256
    assert numerics.RPL_ADMINLOC1 == 257
    assert numerics.RPL_ADMINLOC2 == 258
    assert numerics.RPL_ADMINEMAIL == 259
